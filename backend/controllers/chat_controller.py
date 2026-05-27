"""controllers/chat_controller.py"""

import os
from datetime import datetime

import requests
from bson import ObjectId
from flask import jsonify, request

from utils.db import get_db
from utils.jwt_utils import role_required, token_required

CANCER_KB = {
    'symptoms': {
        'keywords': ['symptom', 'sign', 'pain', 'lump', 'cough', 'fatigue', 'weight loss'],
        'response': (
            "Common warning signs can include unexplained weight loss, persistent fatigue, "
            "new lumps, unusual bleeding, ongoing cough, or changes in bowel habits. "
            "These do not always mean cancer, but persistent symptoms should be checked by a doctor."
        )
    },
    'prevention': {
        'keywords': ['prevent', 'avoid', 'risk', 'protect'],
        'response': (
            "Risk reduction steps include avoiding tobacco, limiting alcohol, staying active, "
            "maintaining a healthy weight, eating a balanced diet, and keeping up with screening."
        )
    },
    'treatment': {
        'keywords': ['treatment', 'therapy', 'chemo', 'surgery', 'radiation', 'immunotherapy'],
        'response': (
            "Treatment depends on cancer type and stage. Common options include surgery, "
            "chemotherapy, radiation therapy, immunotherapy, hormone therapy, and targeted therapy."
        )
    },
    'screening': {
        'keywords': ['screen', 'mammogram', 'colonoscopy', 'pap', 'scan', 'biopsy'],
        'response': (
            "Screening recommendations vary by age and risk profile. Mammograms, Pap smears, "
            "colonoscopies, and low-dose CT scans are common examples."
        )
    },
    'mental_health': {
        'keywords': ['stress', 'anxiety', 'depression', 'cope', 'worried', 'scared'],
        'response': (
            "Feeling worried or overwhelmed is common. Support groups, counseling, exercise, "
            "and help from family or clinicians can make a real difference."
        )
    },
}

DEFAULT_RESPONSE = (
    "I'm Alpha-Cure's AI assistant. You can ask about cancer symptoms, prevention, "
    "screening, treatment options, nutrition, and emotional support."
)


def _rule_based_response(message: str) -> str:
    message_lower = message.lower()
    for topic in CANCER_KB.values():
        if any(keyword in message_lower for keyword in topic['keywords']):
            return topic['response']
    return DEFAULT_RESPONSE


def _groq_response(message: str, context: list | None = None) -> str | None:
    api_key = os.getenv('GROQ_API_KEY')
    model = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')
    if not api_key or api_key == 'your_groq_api_key_here':
        return None

    try:
        messages = [{
            'role': 'system',
            'content': (
                "You are Alpha-Cure's medical AI assistant. Be accurate, calm, and concise. "
                "Do not diagnose. Encourage users to consult a doctor for personal treatment decisions."
            ),
        }]
        if context:
            messages.extend(context[-6:])
        messages.append({'role': 'user', 'content': message})

        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': model,
                'messages': messages,
                'max_tokens': 500,
                'temperature': 0.7,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as exc:
        print(f'[Groq Error] {exc}')
        return None


def _maybe_object_id(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


def _serialize_user(user):
    if not user:
        return None
    return {
        'id': str(user['_id']),
        'name': user.get('name'),
        'email': user.get('email'),
        'phone': user.get('phone'),
        'role': user.get('role'),
        'specialization': user.get('specialization'),
    }


def _room_belongs_to_user(room, user_id):
    return room and user_id in {room.get('patient_id'), room.get('doctor_id')}


def _get_room_for_user(db, room_id, user_id):
    room_obj_id = _maybe_object_id(room_id)
    room = db.chat_rooms.find_one({'_id': room_obj_id}) if room_obj_id else None
    if room and _room_belongs_to_user(room, user_id):
        return room
    return None


def _serialize_room(db, room):
    patient = db.users.find_one({'_id': _maybe_object_id(room.get('patient_id'))}, {'password': 0})
    doctor = db.users.find_one({'_id': _maybe_object_id(room.get('doctor_id'))}, {'password': 0})
    return {
        '_id': str(room['_id']),
        'patient_id': room.get('patient_id'),
        'doctor_id': room.get('doctor_id'),
        'status': room.get('status', 'active'),
        'created_at': room.get('created_at').isoformat() if room.get('created_at') else None,
        'patient': _serialize_user(patient),
        'doctor': _serialize_user(doctor),
    }


@token_required
def ai_chatbot():
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    context = data.get('context', [])

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    response_text = _groq_response(message, context)
    provider = 'groq'
    if not response_text:
        response_text = _rule_based_response(message)
        provider = 'rule-based'

    db = get_db()
    user_obj_id = _maybe_object_id(request.user_id)
    db.chatbot_history.insert_one({
        'user_id': user_obj_id or request.user_id,
        'user_message': message,
        'bot_response': response_text,
        'timestamp': datetime.utcnow(),
    })

    return jsonify({
        'response': response_text,
        'timestamp': datetime.utcnow().isoformat(),
        'provider': provider,
    }), 200


@token_required
def get_chat_rooms():
    db = get_db()
    query = {'patient_id': request.user_id} if request.user_role == 'patient' else {'doctor_id': request.user_id}
    rooms = list(db.chat_rooms.find(query, sort=[('created_at', -1)]))
    return jsonify({'rooms': [_serialize_room(db, room) for room in rooms]}), 200


@role_required('patient')
def create_room():
    data = request.get_json() or {}
    doctor_id = data.get('doctor_id')
    if not doctor_id:
        return jsonify({'error': 'doctor_id required'}), 400

    db = get_db()
    doctor = db.users.find_one({'_id': _maybe_object_id(doctor_id), 'role': 'doctor'})
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    existing = db.chat_rooms.find_one({
        'patient_id': request.user_id,
        'doctor_id': doctor_id,
    })
    if existing:
        return jsonify({
            'room_id': str(existing['_id']),
            'room': _serialize_room(db, existing),
        }), 200

    result = db.chat_rooms.insert_one({
        'patient_id': request.user_id,
        'doctor_id': doctor_id,
        'created_at': datetime.utcnow(),
        'status': 'active',
    })
    room = db.chat_rooms.find_one({'_id': result.inserted_id})
    return jsonify({
        'room_id': str(result.inserted_id),
        'room': _serialize_room(db, room),
    }), 201


@token_required
def get_messages(room_id):
    db = get_db()
    room = _get_room_for_user(db, room_id, request.user_id)
    if not room:
        return jsonify({'error': 'Chat room not found'}), 404

    messages = list(db.messages.find({'room_id': room_id}, sort=[('timestamp', 1)], limit=100))
    for message in messages:
        message['_id'] = str(message['_id'])
        message['sender_id'] = str(message['sender_id'])
        message['timestamp'] = message['timestamp'].isoformat()

    return jsonify({
        'room': _serialize_room(db, room),
        'messages': messages,
    }), 200
