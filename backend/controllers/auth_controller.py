"""controllers/auth_controller.py"""

import bcrypt
from flask import request, jsonify
from datetime import datetime

from utils.db import get_db
from utils.jwt_utils import generate_token


def signup():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'patient')  # 'patient' or 'doctor'
    phone = data.get('phone', '')
    specialization = data.get('specialization', '')  # for doctors

    if not all([name, email, password]):
        return jsonify({'error': 'Name, email and password are required'}), 400

    if role not in ['patient', 'doctor']:
        return jsonify({'error': 'Invalid role'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    db = get_db()

    existing = db.users.find_one({'email': email})
    if existing:
        return jsonify({'error': 'Email already registered'}), 409

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user_doc = {
        'name': name,
        'email': email,
        'password': hashed,
        'role': role,
        'phone': phone,
        'specialization': specialization,
        'is_verified': True,
        'created_at': datetime.utcnow(),
        'profile': {
            'age': None,
            'gender': None,
            'blood_group': None,
            'address': None,
            'emergency_contact': None,
        },
        'medical_history': [],
        'prediction_history': [],
    }

    result = db.users.insert_one(user_doc)
    user_id = result.inserted_id
    token = generate_token(str(user_id), role)

    return jsonify({
        'message': 'Account created successfully',
        'token': token,
        'user': {
            'id': str(user_id),
            'name': name,
            'email': email,
            'role': role,
            'phone': phone,
            'specialization': specialization,
        }
    }), 201


def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    db = get_db()
    user = db.users.find_one({'email': email})

    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    if not bcrypt.checkpw(password.encode(), user['password'].encode()):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = generate_token(str(user['_id']), user['role'])

    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': str(user['_id']),
            'name': user['name'],
            'email': user['email'],
            'role': user['role'],
            'phone': user.get('phone'),
            'specialization': user.get('specialization'),
        }
    }), 200


def logout():
    return jsonify({'message': 'Logged out successfully'}), 200
