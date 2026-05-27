"""utils/jwt_utils.py - JWT token helpers"""

import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

SECRET = os.getenv('JWT_SECRET', 'alpha-cure-secret')
EXPIRY_DAYS = int(os.getenv('JWT_EXPIRY_DAYS', 7))


def generate_token(user_id: str, role: str) -> str:
    payload = {
        'user_id': str(user_id),
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=EXPIRY_DAYS),
        'iat': datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET, algorithms=['HS256'])


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth[7:]
        if not token:
            return jsonify({'error': 'Authentication token missing'}), 401
        try:
            data = decode_token(token)
            request.user_id = data['user_id']
            request.user_role = data['role']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            auth = request.headers.get('Authorization', '')
            if auth.startswith('Bearer '):
                token = auth[7:]
            if not token:
                return jsonify({'error': 'Authentication token missing'}), 401
            try:
                data = decode_token(token)
                if data['role'] not in roles:
                    return jsonify({'error': 'Access denied'}), 403
                request.user_id = data['user_id']
                request.user_role = data['role']
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401
            return f(*args, **kwargs)
        return decorated
    return decorator
