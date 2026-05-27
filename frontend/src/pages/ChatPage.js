import React, { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Activity, Bot, Brain, FileText, Loader, MapPin, MessageCircle,
  Send, Stethoscope, User, X
} from 'lucide-react';
import toast from 'react-hot-toast';

import Sidebar from '../components/common/Sidebar';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { connectSocket, disconnectSocket } from '../services/socket';
import { openRazorpayCheckout } from '../utils/razorpayCheckout';

const PATIENT_NAV = [
  { to: '/dashboard', icon: Activity, label: 'Dashboard' },
  { to: '/predict', icon: Brain, label: 'Cancer Detection' },
  { to: '/reports', icon: FileText, label: 'My Reports' },
  { to: '/chat', icon: MessageCircle, label: 'Chat & Consult' },
  { to: '/hospitals', icon: MapPin, label: 'Nearby Hospitals' },
  { to: '/profile', icon: User, label: 'My Profile' },
];

const DOCTOR_NAV = [
  { to: '/doctor', icon: Activity, label: 'Dashboard' },
  { to: '/chat', icon: MessageCircle, label: 'Patient Chat' },
  { to: '/profile', icon: User, label: 'My Profile' },
];

const QUICK_QUESTIONS = [
  'What are common cancer symptoms?',
  'How can I reduce cancer risk?',
  'What screening tests are important?',
  'What are common treatment options?',
  'How do I cope with anxiety during treatment?',
];

function useChatSocket(token, userName) {
  const socketRef = useRef(null);
  const currentRoomRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  const connectToRoom = (roomId, handlers) => {
    const socket = connectSocket();
    socketRef.current = socket;
    if (currentRoomRef.current && currentRoomRef.current !== roomId) {
      socket.emit('leave_room', { room_id: currentRoomRef.current });
    }
    currentRoomRef.current = roomId;

    socket.off('receive_message');
    socket.off('user_typing');
    socket.off('user_stop_typing');
    socket.off('error');

    socket.on('receive_message', handlers.onMessage);
    socket.on('user_typing', handlers.onTyping);
    socket.on('user_stop_typing', handlers.onStopTyping);
    socket.on('error', handlers.onError);
    socket.emit('join_room', { token, room_id: roomId });
  };

  const leaveRoom = (roomId) => {
    const targetRoom = roomId || currentRoomRef.current;
    if (targetRoom) socketRef.current?.emit('leave_room', { room_id: targetRoom });
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    disconnectSocket();
    socketRef.current = null;
    currentRoomRef.current = null;
  };

  const sendMessage = (roomId, message) => {
    socketRef.current?.emit('send_message', { token, room_id: roomId, message });
  };

  const emitTyping = (roomId) => {
    if (!socketRef.current || !roomId) return;
    socketRef.current.emit('typing', { room_id: roomId, user_name: userName });
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = setTimeout(() => {
      socketRef.current?.emit('stop_typing', { room_id: roomId });
    }, 1200);
  };

  useEffect(() => () => leaveRoom(null), []);

  return { connectToRoom, leaveRoom, sendMessage, emitTyping };
}

function ChatMessages({ messages, currentUserId, emptyText, typingLabel }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typingLabel]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-3">
      {messages.length === 0 && (
        <div className="text-center py-8 text-slate-400 text-sm">
          <MessageCircle className="w-8 h-8 mx-auto mb-2 opacity-30" />
          {emptyText}
        </div>
      )}

      {messages.map((msg, index) => {
        const isMe = String(msg.sender_id) === String(currentUserId);
        return (
          <div key={`${msg._id || index}-${msg.timestamp || index}`} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[75%] px-4 py-2.5 rounded-2xl text-sm ${
              isMe ? 'bg-primary-600 text-white rounded-tr-none' : 'bg-white border border-slate-100 text-slate-700 rounded-tl-none'
            }`}>
              {msg.content}
              <p className={`text-xs mt-1 ${isMe ? 'text-primary-200' : 'text-slate-400'}`}>
                {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
              </p>
            </div>
          </div>
        );
      })}

      {typingLabel && (
        <div className="text-xs text-slate-400 px-1">{typingLabel}</div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}

function AIChatbot() {
  const [messages, setMessages] = useState([{
    role: 'bot',
    content: "Hi! I'm Alpha-Cure's AI assistant. Ask me about symptoms, prevention, screening, treatment, or emotional support.",
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (text) => {
    const message = text || input.trim();
    if (!message || loading) return;

    setInput('');
    setMessages(prev => [...prev, {
      role: 'user',
      content: message,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }]);
    setLoading(true);

    const context = messages
      .slice(-6)
      .map(msg => ({ role: msg.role === 'bot' ? 'assistant' : 'user', content: msg.content }));

    try {
      const res = await api.post('/chat/ai', { message, context });
      setMessages(prev => [...prev, {
        role: 'bot',
        content: res.data.response,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'bot',
        content: 'Sorry, I could not answer right now. Please try again.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <div key={index} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'bot' ? 'bg-primary-100' : 'bg-teal-100'}`}>
              {msg.role === 'bot' ? <Bot className="w-4 h-4 text-primary-600" /> : <User className="w-4 h-4 text-teal-600" />}
            </div>
            <div className={`max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col`}>
              <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-line ${
                msg.role === 'bot' ? 'bg-white border border-slate-100 text-slate-700 rounded-tl-none' : 'bg-primary-600 text-white rounded-tr-none'
              }`}>
                {msg.content}
              </div>
              <span className="text-xs text-slate-400 mt-1 px-1">{msg.time}</span>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-primary-600" />
            </div>
            <div className="bg-white border border-slate-100 rounded-2xl rounded-tl-none px-4 py-3">
              <div className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <div key={i} className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="px-4 pb-2 flex gap-2 overflow-x-auto scrollbar-none">
        {QUICK_QUESTIONS.map(question => (
          <button
            key={question}
            onClick={() => send(question)}
            className="flex-shrink-0 text-xs px-3 py-1.5 rounded-full border border-primary-200 bg-primary-50 text-primary-700 hover:bg-primary-100 transition-colors"
          >
            {question}
          </button>
        ))}
      </div>

      <div className="p-4 border-t border-slate-100">
        <div className="flex gap-3 items-end">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder="Ask a health question..."
            rows={1}
            className="input-field flex-1 resize-none py-2.5"
            style={{ minHeight: '44px', maxHeight: '120px' }}
          />
          <button onClick={() => send()} disabled={!input.trim() || loading} className="btn-primary px-4 py-2.5 flex-shrink-0 disabled:opacity-40">
            {loading ? <Loader className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
}

function PatientDoctorChat({ doctors, doctorsLoading }) {
  const { user, token } = useAuth();
  const [rooms, setRooms] = useState([]);
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [roomId, setRoomId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [requesting, setRequesting] = useState(false);
  const [typingLabel, setTypingLabel] = useState('');
  const [roomsLoading, setRoomsLoading] = useState(true);
  const socket = useChatSocket(token, user?.name || 'Patient');

  const loadRooms = async () => {
    try {
      setRoomsLoading(true);
      const res = await api.get('/chat/rooms');
      setRooms(res.data.rooms || []);
    } catch {
      setRooms([]);
    } finally {
      setRoomsLoading(false);
    }
  };

  useEffect(() => {
    loadRooms();
  }, []);

  const openRoom = async (room, doctorOverride = null) => {
    try {
      const res = await api.get(`/chat/messages/${room._id}`);
      setSelectedDoctor(doctorOverride || room.doctor);
      setRoomId(room._id);
      setMessages(res.data.messages || []);
      setTypingLabel('');
      socket.connectToRoom(room._id, {
        onMessage: msg => setMessages(prev => [...prev, msg]),
        onTyping: data => setTypingLabel(`${data.user_name || 'Doctor'} is typing...`),
        onStopTyping: () => setTypingLabel(''),
        onError: err => toast.error(err.message || 'Chat error'),
      });
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to open chat');
    }
  };

  const requestConsultation = async (doctor) => {
    const doctorId = doctor.id || doctor._id;
    setRequesting(true);
    try {
      const orderRes = await api.post('/doctor/consultation/create-order', { doctor_id: doctorId });
      const order = orderRes.data;

      const payment = await openRazorpayCheckout({
        order,
        user,
        doctor,
        onDismiss: () => setRequesting(false),
      });

      const verifyRes = await api.post('/doctor/consultation/verify-payment', {
        doctor_id: doctorId,
        razorpay_order_id: payment.razorpay_order_id,
        razorpay_payment_id: payment.razorpay_payment_id,
        razorpay_signature: payment.razorpay_signature,
      });

      await loadRooms();
      const room = verifyRes.data.room || { _id: verifyRes.data.room_id, doctor };
      toast.success(`Payment successful. Chat opened with Dr. ${doctor.name}`);
      openRoom(room, doctor);
    } catch (err) {
      if (err.message === 'Payment cancelled') {
        toast('Payment cancelled', { icon: 'ℹ️' });
      } else if (err.response?.data?.code === 'PAYMENT_NOT_CONFIGURED') {
        toast.error('Payment is not configured on the server. Add Razorpay keys to backend/.env.');
      } else if (err.response?.data?.code === 'CONSULTATION_EXISTS') {
        toast.error(err.response.data.error);
        await loadRooms();
      } else {
        toast.error(err.response?.data?.error || err.message || 'Payment failed');
      }
    } finally {
      setRequesting(false);
    }
  };

  const sendMessage = () => {
    const message = input.trim();
    if (!message || !roomId) return;
    socket.sendMessage(roomId, message);
    setInput('');
  };

  const handleInputChange = (value) => {
    setInput(value);
    if (value.trim()) socket.emitTyping(roomId);
  };

  const leaveChat = () => {
    socket.leaveRoom(roomId);
    setSelectedDoctor(null);
    setRoomId(null);
    setMessages([]);
    setTypingLabel('');
  };

  const roomByDoctorId = new Map(rooms.map(room => [room.doctor_id, room]));

  if (!selectedDoctor) {
    return (
      <div className="p-4">
        <div className="mb-4 p-3 rounded-xl bg-amber-50 border border-amber-100">
          <p className="text-sm text-amber-700 font-medium">Real-time doctor consultation for Rs. 5</p>
          <p className="text-xs text-amber-600 mt-0.5">
            Pay securely via Razorpay to start chatting. After payment, you can return anytime and open the same chat room.
          </p>
        </div>

        <div className="space-y-3">
          {doctorsLoading || roomsLoading ? (
            <div className="text-center py-10 text-slate-400">
              <Loader className="w-8 h-8 mx-auto mb-3 animate-spin opacity-60" />
              <p className="text-sm">Loading available doctors...</p>
            </div>
          ) : doctors.length === 0 ? (
            <div className="text-center py-10 text-slate-400">
              <Stethoscope className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm">No doctors available right now</p>
              <p className="text-xs mt-1">Create or log in to a doctor account, then refresh this page.</p>
            </div>
          ) : doctors.map(doctor => {
            const doctorId = doctor.id || doctor._id;
            const existingRoom = roomByDoctorId.get(doctorId);
            return (
              <div key={doctorId} className="card flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-400 to-primary-400 flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
                  {doctor.name?.[0]}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-slate-900">Dr. {doctor.name}</p>
                  <p className="text-sm text-primary-600">{doctor.specialization || 'Oncology'}</p>
                  <p className="text-xs text-slate-400 mt-1">
                    {existingRoom ? 'Existing consultation available' : 'Start a new consultation'}
                  </p>
                </div>
                <button
                  onClick={() => existingRoom ? openRoom(existingRoom, doctor) : requestConsultation(doctor)}
                  disabled={requesting}
                  className="btn-primary text-sm px-4 py-2"
                >
                  {requesting ? <Loader className="w-4 h-4 animate-spin" /> : existingRoom ? 'Open Chat' : 'Consult Rs. 5'}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-slate-100 flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-400 to-primary-400 flex items-center justify-center text-white font-bold flex-shrink-0">
          {selectedDoctor.name?.[0]}
        </div>
        <div className="flex-1">
          <p className="font-semibold text-slate-900 text-sm">Dr. {selectedDoctor.name}</p>
          <p className="text-xs text-green-600">{typingLabel || 'Live chat connected'}</p>
        </div>
        <button onClick={leaveChat} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500">
          <X className="w-4 h-4" />
        </button>
      </div>

      <ChatMessages
        messages={messages}
        currentUserId={user?.id}
        emptyText={`Start your consultation with Dr. ${selectedDoctor.name}`}
        typingLabel=""
      />

      <div className="p-3 border-t border-slate-100 flex gap-2">
        <input
          value={input}
          onChange={e => handleInputChange(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') sendMessage(); }}
          placeholder="Type your message..."
          className="input-field flex-1 py-2"
        />
        <button onClick={sendMessage} className="btn-primary px-3 py-2">
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function DoctorPatientChat({ initialPatientId }) {
  const { user, token } = useAuth();
  const [rooms, setRooms] = useState([]);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [typingLabel, setTypingLabel] = useState('');
  const [loading, setLoading] = useState(true);
  const socket = useChatSocket(token, user?.name || 'Doctor');

  const loadRooms = async () => {
    setLoading(true);
    try {
      const res = await api.get('/chat/rooms');
      const nextRooms = res.data.rooms || [];
      setRooms(nextRooms);

      if (nextRooms.length === 0) {
        setSelectedRoom(null);
        setMessages([]);
        return;
      }

      const preferredRoom = initialPatientId
        ? nextRooms.find(room => room.patient_id === initialPatientId)
        : null;

      if (!selectedRoom) {
        openRoom(preferredRoom || nextRooms[0], nextRooms);
      }
    } catch {
      toast.error('Failed to load patient chats');
      setRooms([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRooms();
  }, [initialPatientId]);

  const openRoom = async (room, roomList = rooms) => {
    if (!room) return;

    try {
      const res = await api.get(`/chat/messages/${room._id}`);
      const fullRoom = res.data.room || roomList.find(item => item._id === room._id) || room;
      setSelectedRoom(fullRoom);
      setMessages(res.data.messages || []);
      setTypingLabel('');

      socket.connectToRoom(fullRoom._id, {
        onMessage: msg => setMessages(prev => [...prev, msg]),
        onTyping: data => setTypingLabel(`${data.user_name || 'Patient'} is typing...`),
        onStopTyping: () => setTypingLabel(''),
        onError: err => toast.error(err.message || 'Chat error'),
      });
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to open patient chat');
    }
  };

  const sendMessage = () => {
    const message = input.trim();
    if (!message || !selectedRoom) return;
    socket.sendMessage(selectedRoom._id, message);
    setInput('');
  };

  const handleInputChange = (value) => {
    setInput(value);
    if (value.trim() && selectedRoom) socket.emitTyping(selectedRoom._id);
  };

  return (
    <div className="grid lg:grid-cols-[320px,1fr] h-full">
      <div className="border-r border-slate-100 bg-slate-50/70">
        <div className="p-4 border-b border-slate-100 bg-white">
          <h2 className="font-bold text-slate-900">Patient Conversations</h2>
          <p className="text-xs text-slate-500 mt-1">Only patients who opened a consultation appear here.</p>
        </div>

        <div className="p-3 space-y-2 overflow-y-auto" style={{ height: 'calc(100% - 73px)' }}>
          {loading ? (
            <div className="flex items-center justify-center py-10">
              <Loader className="w-5 h-5 animate-spin text-primary-500" />
            </div>
          ) : rooms.length === 0 ? (
            <div className="text-center py-10 text-slate-400 text-sm">
              <MessageCircle className="w-8 h-8 mx-auto mb-2 opacity-30" />
              No patient chats yet
              <p className="text-xs mt-2">A patient must open a consultation from the Doctor Chat tab first.</p>
            </div>
          ) : rooms.map(room => {
            const patient = room.patient || {};
            const active = selectedRoom?._id === room._id;
            return (
              <button
                key={room._id}
                onClick={() => openRoom(room)}
                className={`w-full text-left p-3 rounded-2xl border transition-colors ${
                  active ? 'bg-primary-50 border-primary-200' : 'bg-white border-slate-100 hover:border-primary-100'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-teal-400 flex items-center justify-center text-white font-bold flex-shrink-0">
                    {patient.name?.[0] || 'P'}
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-slate-900 text-sm truncate">{patient.name || 'Patient'}</p>
                    <p className="text-xs text-slate-500 truncate">{patient.email || 'Consultation room'}</p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex flex-col">
        {selectedRoom ? (
          <>
            <div className="p-3 border-b border-slate-100 flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-400 to-teal-400 flex items-center justify-center text-white font-bold flex-shrink-0">
                {selectedRoom.patient?.name?.[0] || 'P'}
              </div>
              <div className="flex-1">
                <p className="font-semibold text-slate-900 text-sm">{selectedRoom.patient?.name || 'Patient'}</p>
                <p className="text-xs text-slate-500">{typingLabel || selectedRoom.patient?.email || 'Live consultation'}</p>
              </div>
            </div>

            <ChatMessages
              messages={messages}
              currentUserId={user?.id}
              emptyText={`Start chatting with ${selectedRoom.patient?.name || 'this patient'}`}
              typingLabel=""
            />

            <div className="p-3 border-t border-slate-100 flex gap-2">
              <input
                value={input}
                onChange={e => handleInputChange(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') sendMessage(); }}
                placeholder="Reply to patient..."
                className="input-field flex-1 py-2"
              />
              <button onClick={sendMessage} className="btn-primary px-3 py-2">
                <Send className="w-4 h-4" />
              </button>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
            Select a patient conversation to begin
          </div>
        )}
      </div>
    </div>
  );
}

export default function ChatPage() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState('ai');
  const [doctors, setDoctors] = useState([]);
  const [doctorsLoading, setDoctorsLoading] = useState(false);

  const isDoctor = user?.role === 'doctor';
  const navItems = isDoctor ? DOCTOR_NAV : PATIENT_NAV;

  useEffect(() => {
    if (isDoctor) return;
    setDoctorsLoading(true);
    api.get('/doctor/list')
      .then(res => setDoctors(res.data.doctors || []))
      .catch(err => {
        setDoctors([]);
        toast.error(err.response?.data?.error || 'Failed to load doctors');
      })
      .finally(() => setDoctorsLoading(false));
  }, [isDoctor]);

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar navItems={navItems} role={user?.role} />
      <main className="lg:ml-64 pt-14 lg:pt-0">
        <div className="max-w-6xl mx-auto p-6">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-slate-900">
              {isDoctor ? 'Patient Chats' : 'Chat & Consultation'}
            </h1>
            <p className="text-slate-500 text-sm mt-1">
              {isDoctor
                ? 'Manage your live conversations with patients.'
                : 'Talk to the AI assistant or start a live consultation with a doctor.'}
            </p>
          </div>

          <div className="card p-0 overflow-hidden" style={{ height: 'calc(100vh - 180px)', minHeight: '520px' }}>
            {isDoctor ? (
              <DoctorPatientChat initialPatientId={searchParams.get('patient')} />
            ) : (
              <>
                <div className="flex border-b border-slate-100">
                  {[
                    { id: 'ai', label: 'AI Chatbot', icon: Bot },
                    { id: 'doctor', label: 'Doctor Chat', icon: Stethoscope },
                  ].map(({ id, label, icon: Icon }) => (
                    <button
                      key={id}
                      onClick={() => setActiveTab(id)}
                      className={`flex items-center gap-2 px-6 py-4 text-sm font-semibold border-b-2 transition-colors ${
                        activeTab === id ? 'border-primary-500 text-primary-700 bg-primary-50/50' : 'border-transparent text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      <Icon className="w-4 h-4" /> {label}
                    </button>
                  ))}
                </div>

                <div className="flex flex-col" style={{ height: 'calc(100% - 57px)' }}>
                  {activeTab === 'ai' ? <AIChatbot /> : <PatientDoctorChat doctors={doctors} doctorsLoading={doctorsLoading} />}
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
