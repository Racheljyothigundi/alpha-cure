"""services/socket_service.py - Real-time chat with Socket.IO"""

from datetime import datetime

from bson import ObjectId
from flask_socketio import emit, join_room, leave_room

from utils.db import get_db
from utils.jwt_utils import decode_token


def _normalize_payload(data):
    return data if isinstance(data, dict) else {}


def _maybe_object_id(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


def _get_authorized_room(db, room_id, user_id):
    room_obj_id = _maybe_object_id(room_id)
    room = db.chat_rooms.find_one({'_id': room_obj_id}) if room_obj_id else None
    if not room:
        return None
    if user_id not in {room.get('patient_id'), room.get('doctor_id')}:
        return None
    return room


def register_socket_events(socketio):

    @socketio.on('connect')
    def on_connect(auth=None):
        print('[Socket] Client connected')

    @socketio.on('disconnect')
    def on_disconnect():
        print('[Socket] Client disconnected')

    @socketio.on('join_room')
    def on_join(data):
        data = _normalize_payload(data)
        token = data.get('token')
        room_id = str(data.get('room_id', '')).strip()

        if not token or not room_id:
            emit('error', {'message': 'token and room_id are required'})
            return

        try:
            payload = decode_token(token)
            db = get_db()
            room = _get_authorized_room(db, room_id, payload['user_id'])
            if not room:
                emit('error', {'message': 'Room not found or access denied'})
                return

            join_room(room_id)
            emit('room_joined', {
                'room_id': room_id,
                'user_id': payload['user_id'],
                'message': 'Joined room successfully',
            }, room=room_id)
        except Exception as exc:
            emit('error', {'message': str(exc)})

    @socketio.on('leave_room')
    def on_leave(data):
        data = _normalize_payload(data)
        room_id = str(data.get('room_id', '')).strip()
        if not room_id:
            emit('error', {'message': 'room_id is required'})
            return
        leave_room(room_id)

    @socketio.on('send_message')
    def on_message(data):
        data = _normalize_payload(data)
        token = data.get('token')
        room_id = str(data.get('room_id', '')).strip()
        content = str(data.get('message', '')).strip()

        if not token or not room_id or not content:
            emit('error', {'message': 'token, room_id, and message are required'})
            return

        try:
            payload = decode_token(token)
            db = get_db()
            room = _get_authorized_room(db, room_id, payload['user_id'])
            if not room:
                emit('error', {'message': 'Room not found or access denied'})
                return

            msg_doc = {
                'room_id': room_id,
                'sender_id': payload['user_id'],
                'sender_role': payload['role'],
                'content': content,
                'timestamp': datetime.utcnow(),
                'read': False,
            }
            result = db.messages.insert_one(msg_doc)
            msg_doc['_id'] = str(result.inserted_id)
            msg_doc['timestamp'] = msg_doc['timestamp'].isoformat()

            emit('receive_message', msg_doc, room=room_id)
        except Exception as exc:
            emit('error', {'message': str(exc)})

    @socketio.on('typing')
    def on_typing(data):
        data = _normalize_payload(data)
        room_id = str(data.get('room_id', '')).strip()
        user_name = str(data.get('user_name', 'Someone')).strip() or 'Someone'
        if not room_id:
            return
        emit('user_typing', {'user_name': user_name}, room=room_id, include_self=False)

    @socketio.on('stop_typing')
    def on_stop_typing(data):
        data = _normalize_payload(data)
        room_id = str(data.get('room_id', '')).strip()
        if not room_id:
            return
        emit('user_stop_typing', {}, room=room_id, include_self=False)
