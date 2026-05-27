"""controllers/doctor_controller.py"""

from flask import request, jsonify
from bson import ObjectId
from datetime import datetime

from utils.db import get_db
from utils.jwt_utils import token_required, role_required
from services.razorpay_service import (
    get_razorpay_client,
    verify_payment_signature,
    CONSULTATION_AMOUNT_INR,
    CONSULTATION_AMOUNT_PAISE,
)


@role_required('patient')
def get_all_doctors():
    db = get_db()
    doctors = list(db.users.find({'role': 'doctor', 'is_verified': True},
                                  {'password': 0, 'prediction_history': 0}))
    for d in doctors:
        d['_id'] = str(d['_id'])
    return jsonify({'doctors': doctors}), 200


@role_required('doctor')
def get_cancer_patients():
    """Doctor: get all patients with high/critical risk predictions."""
    db = get_db()
    high_risk_preds = list(db.predictions.find(
        {'risk_level': {'$in': ['HIGH', 'CRITICAL']}},
        sort=[('timestamp', -1)]
    ))

    patient_map = {}
    for pred in high_risk_preds:
        uid = str(pred['user_id'])
        if uid not in patient_map:
            user = db.users.find_one({'_id': pred['user_id']}, {'password': 0})
            if user:
                patient_map[uid] = {
                    'id': uid,
                    'name': user['name'],
                    'email': user['email'],
                    'phone': user.get('phone'),
                    'predictions': []
                }
        if uid in patient_map:
            patient_map[uid]['predictions'].append({
                'id': str(pred['_id']),
                'label': pred['label'],
                'confidence': pred['confidence'],
                'risk_level': pred['risk_level'],
                'date': pred['timestamp'].isoformat()
            })

    return jsonify({'patients': list(patient_map.values())}), 200


@role_required('doctor')
def get_doctor_stats():
    db = get_db()
    total_patients = db.users.count_documents({'role': 'patient', 'is_verified': True})
    total_predictions = db.predictions.count_documents({})
    high_risk = db.predictions.count_documents({'risk_level': {'$in': ['HIGH', 'CRITICAL']}})
    consultations = db.consultations.count_documents({'doctor_id': request.user_id})

    return jsonify({
        'total_patients': total_patients,
        'total_predictions': total_predictions,
        'high_risk_patients': high_risk,
        'consultations_accepted': consultations,
    }), 200


def _activate_consultation_and_room(db, patient_id, doctor_id, doctor, payment_meta):
    """Mark consultation paid and ensure chat room exists."""
    db.consultations.update_one(
        {
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'razorpay_order_id': payment_meta['razorpay_order_id'],
        },
        {'$set': {
            'payment_status': 'paid',
            'status': 'active',
            'razorpay_payment_id': payment_meta.get('razorpay_payment_id'),
            'paid_at': datetime.utcnow(),
        }},
    )

    db.chat_rooms.update_one(
        {'patient_id': patient_id, 'doctor_id': doctor_id},
        {'$setOnInsert': {
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'created_at': datetime.utcnow(),
            'status': 'active',
        }},
        upsert=True,
    )
    room = db.chat_rooms.find_one({'patient_id': patient_id, 'doctor_id': doctor_id})
    consultation = db.consultations.find_one({
        'patient_id': patient_id,
        'doctor_id': doctor_id,
        'razorpay_order_id': payment_meta['razorpay_order_id'],
    })
    return room, consultation


@role_required('patient')
def create_consultation_order():
    """Create a Razorpay order for Rs. 5 doctor consultation."""
    data = request.get_json() or {}
    doctor_id = data.get('doctor_id')
    if not doctor_id:
        return jsonify({'error': 'doctor_id required'}), 400

    client, key_id = get_razorpay_client()
    if not client:
        return jsonify({
            'error': 'Payment gateway is not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to backend/.env.',
            'code': 'PAYMENT_NOT_CONFIGURED',
        }), 503

    db = get_db()
    doctor = db.users.find_one({'_id': ObjectId(doctor_id), 'role': 'doctor'})
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    existing_room = db.chat_rooms.find_one({
        'patient_id': request.user_id,
        'doctor_id': doctor_id,
    })
    if existing_room:
        return jsonify({
            'error': 'You already have an active consultation with this doctor.',
            'code': 'CONSULTATION_EXISTS',
            'room_id': str(existing_room['_id']),
        }), 409

    pending = db.consultations.find_one({
        'patient_id': request.user_id,
        'doctor_id': doctor_id,
        'payment_status': 'pending',
    })
    if pending and pending.get('razorpay_order_id'):
        return jsonify({
            'order_id': pending['razorpay_order_id'],
            'amount': pending.get('amount', CONSULTATION_AMOUNT_INR),
            'currency': pending.get('currency', 'INR'),
            'key_id': key_id,
            'consultation_id': str(pending['_id']),
        }), 200

    try:
        order = client.order.create({
            'amount': CONSULTATION_AMOUNT_PAISE,
            'currency': 'INR',
            'receipt': f"consult_{request.user_id[:8]}_{doctor_id[:8]}",
            'notes': {
                'patient_id': request.user_id,
                'doctor_id': doctor_id,
                'purpose': 'doctor_consultation',
            },
        })
    except Exception as e:
        return jsonify({'error': f'Failed to create payment order: {e}'}), 502

    result = db.consultations.insert_one({
        'patient_id': request.user_id,
        'doctor_id': doctor_id,
        'status': 'pending',
        'payment_status': 'pending',
        'amount': CONSULTATION_AMOUNT_INR,
        'currency': 'INR',
        'razorpay_order_id': order['id'],
        'requested_at': datetime.utcnow(),
    })

    return jsonify({
        'order_id': order['id'],
        'amount': CONSULTATION_AMOUNT_INR,
        'currency': 'INR',
        'key_id': key_id,
        'consultation_id': str(result.inserted_id),
        'doctor_name': doctor['name'],
    }), 201


@role_required('patient')
def verify_consultation_payment():
    """Verify Razorpay payment and open consultation chat room."""
    data = request.get_json() or {}
    doctor_id = data.get('doctor_id')
    order_id = data.get('razorpay_order_id')
    payment_id = data.get('razorpay_payment_id')
    signature = data.get('razorpay_signature')

    if not all([doctor_id, order_id, payment_id, signature]):
        return jsonify({'error': 'doctor_id and Razorpay payment details are required'}), 400

    db = get_db()
    doctor = db.users.find_one({'_id': ObjectId(doctor_id), 'role': 'doctor'})
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    consultation = db.consultations.find_one({
        'patient_id': request.user_id,
        'doctor_id': doctor_id,
        'razorpay_order_id': order_id,
    })
    if not consultation:
        return jsonify({'error': 'Consultation order not found'}), 404

    if consultation.get('payment_status') == 'paid':
        room = db.chat_rooms.find_one({
            'patient_id': request.user_id,
            'doctor_id': doctor_id,
        })
        return jsonify({
            'message': 'Payment already verified',
            'consultation_id': str(consultation['_id']),
            'room_id': str(room['_id']) if room else None,
            'room': _serialize_room(room, doctor) if room else None,
            'doctor_name': doctor['name'],
        }), 200

    try:
        verify_payment_signature(order_id, payment_id, signature)
    except Exception as e:
        return jsonify({'error': f'Payment verification failed: {e}'}), 400

    payment_meta = {
        'razorpay_order_id': order_id,
        'razorpay_payment_id': payment_id,
    }
    room, consultation = _activate_consultation_and_room(
        db, request.user_id, doctor_id, doctor, payment_meta
    )

    return jsonify({
        'message': 'Payment successful. Consultation is now active.',
        'consultation_id': str(consultation['_id']),
        'room_id': str(room['_id']),
        'room': _serialize_room(room, doctor),
        'doctor_name': doctor['name'],
    }), 200


def _serialize_room(room, doctor):
    if not room:
        return None
    return {
        '_id': str(room['_id']),
        'doctor_id': room.get('doctor_id'),
        'patient_id': room.get('patient_id'),
        'doctor': {
            '_id': str(doctor['_id']),
            'id': str(doctor['_id']),
            'name': doctor.get('name'),
            'specialization': doctor.get('specialization'),
        },
    }


@token_required
def get_consultations():
    db = get_db()
    role = request.user_role
    query = {'doctor_id': request.user_id} if role == 'doctor' else {'patient_id': request.user_id}

    consultations = list(db.consultations.find(query, sort=[('requested_at', -1)]))
    for c in consultations:
        c['_id'] = str(c['_id'])
        c['requested_at'] = c['requested_at'].isoformat()

    return jsonify({'consultations': consultations}), 200
