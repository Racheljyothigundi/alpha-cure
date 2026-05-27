"""
seed_db.py
──────────
Populates MongoDB with demo data for development/testing.
Usage: python seed_db.py

Creates:
  • 1 demo patient account (patient@demo.com / demo1234)
  • 1 demo doctor account  (doctor@demo.com  / demo1234)
  • 5 sample predictions for the patient
  • 1 chat room between patient and doctor
"""

import os
import sys
from datetime import datetime, timedelta
import random
import bcrypt
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from utils.db import init_db

db = init_db()
print("\n🌱 Alpha-Cure Database Seeder")
print("=" * 50)

# ─── Clear existing demo data ─────────────────────────────────────────────────
db.users.delete_many({'email': {'$in': ['patient@demo.com', 'doctor@demo.com']}})
print("Cleared existing demo accounts")

# ─── Create demo users ────────────────────────────────────────────────────────
pw_hash = bcrypt.hashpw(b'demo1234', bcrypt.gensalt()).decode()

patient_id = ObjectId()
doctor_id = ObjectId()

patient = {
    '_id': patient_id,
    'name': 'Priya Sharma',
    'email': 'patient@demo.com',
    'password': pw_hash,
    'role': 'patient',
    'phone': '+91 98765 43210',
    'is_verified': True,
    'created_at': datetime.utcnow() - timedelta(days=30),
    'profile': {
        'age': 42,
        'gender': 'Female',
        'blood_group': 'B+',
        'address': '14 Lajpat Nagar, New Delhi - 110024',
        'emergency_contact': '+91 98765 11111',
    },
    'medical_history': [
        'Hypertension (managed with medication)',
        'Family history: maternal aunt had breast cancer',
    ],
    'prediction_history': [],
}

doctor = {
    '_id': doctor_id,
    'name': 'Arjun Mehta',
    'email': 'doctor@demo.com',
    'password': pw_hash,
    'role': 'doctor',
    'phone': '+91 99887 76655',
    'specialization': 'Oncology',
    'is_verified': True,
    'created_at': datetime.utcnow() - timedelta(days=60),
    'profile': {},
    'medical_history': [],
    'prediction_history': [],
}

db.users.insert_many([patient, doctor])
print(f"✓ Patient created: patient@demo.com (ID: {patient_id})")
print(f"✓ Doctor created:  doctor@demo.com  (ID: {doctor_id})")

# ─── Create predictions ───────────────────────────────────────────────────────
predictions_data = [
    {
        'label': 'Normal (No Cancer Detected)',
        'code': 'NORMAL',
        'risk_level': 'LOW',
        'confidence': 97.3,
        'prediction': 0,
        'features': {'age': 40, 'gender': 0, 'bmi': 23.5, 'smoking': 0,
                     'genetic_risk': 1, 'physical_activity': 4.0, 'alcohol_intake': 1.0,
                     'cancer_history': 0, 'diagnosis': 0},
        'days_ago': 30,
    },
    {
        'label': 'Normal (No Cancer Detected)',
        'code': 'NORMAL',
        'risk_level': 'LOW',
        'confidence': 94.8,
        'prediction': 0,
        'features': {'age': 41, 'gender': 0, 'bmi': 24.1, 'smoking': 0,
                     'genetic_risk': 1, 'physical_activity': 3.5, 'alcohol_intake': 1.5,
                     'cancer_history': 0, 'diagnosis': 0},
        'days_ago': 20,
    },
    {
        'label': 'Benign Tumor',
        'code': 'BENIGN',
        'risk_level': 'MODERATE',
        'confidence': 78.2,
        'prediction': 1,
        'features': {'age': 42, 'gender': 0, 'bmi': 25.3, 'smoking': 0,
                     'genetic_risk': 2, 'physical_activity': 2.0, 'alcohol_intake': 2.0,
                     'cancer_history': 0, 'diagnosis': 0},
        'days_ago': 10,
    },
    {
        'label': 'Malignant - Stage I/II',
        'code': 'MALIGNANT_EARLY',
        'risk_level': 'HIGH',
        'confidence': 82.5,
        'prediction': 2,
        'features': {'age': 42, 'gender': 0, 'bmi': 26.0, 'smoking': 1,
                     'genetic_risk': 2, 'physical_activity': 1.5, 'alcohol_intake': 3.0,
                     'cancer_history': 0, 'diagnosis': 1},
        'days_ago': 5,
    },
    {
        'label': 'Benign Tumor',
        'code': 'BENIGN',
        'risk_level': 'MODERATE',
        'confidence': 71.9,
        'prediction': 1,
        'features': {'age': 42, 'gender': 0, 'bmi': 25.8, 'smoking': 0,
                     'genetic_risk': 2, 'physical_activity': 3.0, 'alcohol_intake': 1.0,
                     'cancer_history': 0, 'diagnosis': 1},
        'days_ago': 1,
    },
]

SUGGESTIONS_MAP = {
    'LOW': ['Continue annual screenings', 'Maintain active lifestyle', 'Balanced diet with antioxidants'],
    'MODERATE': ['Schedule a follow-up with an oncologist within 2 weeks', 'Request biopsy for confirmation', 'Monitor any changes closely'],
    'HIGH': ['⚠️ Consult an oncologist immediately', 'Comprehensive staging workup recommended', 'Seek second opinion from specialist'],
    'CRITICAL': ['🚨 Immediate oncology consultation required', 'Emergency referral to multi-disciplinary team', 'Discuss treatment options urgently'],
}

pred_ids = []
for p in predictions_data:
    pred_id = ObjectId()
    pred_ids.append(pred_id)
    pred_doc = {
        '_id': pred_id,
        'user_id': patient_id,
        'features': p['features'],
        'prediction': p['prediction'],
        'label': p['label'],
        'code': p['code'],
        'confidence': p['confidence'],
        'risk_level': p['risk_level'],
        'probabilities': {},
        'suggestions': SUGGESTIONS_MAP[p['risk_level']],
        'timestamp': datetime.utcnow() - timedelta(days=p['days_ago']),
    }
    db.predictions.insert_one(pred_doc)
    db.users.update_one(
        {'_id': patient_id},
        {'$push': {'prediction_history': {
            'prediction_id': str(pred_id),
            'label': p['label'],
            'confidence': p['confidence'],
            'risk_level': p['risk_level'],
            'date': pred_doc['timestamp'],
        }}}
    )

print(f"✓ Created {len(predictions_data)} sample predictions")

# ─── Create chat room ─────────────────────────────────────────────────────────
room_id = ObjectId()
db.chat_rooms.insert_one({
    '_id': room_id,
    'patient_id': str(patient_id),
    'doctor_id': str(doctor_id),
    'created_at': datetime.utcnow() - timedelta(days=5),
    'status': 'active',
})

# Sample chat messages
messages = [
    ('patient', 'Hello Doctor, I received a HIGH risk result from the AI screening. I am quite worried.'),
    ('doctor', 'Hello Priya. I can see your recent assessment. Please don\'t panic — a HIGH risk classification means we need further investigation, not that you have cancer confirmed.'),
    ('patient', 'What should I do next?'),
    ('doctor', 'I recommend scheduling a biopsy and MRI scan within the next 7 days. I\'ve also noted your family history. Please bring all previous medical records to your appointment.'),
    ('patient', 'Thank you Doctor. Should I stop any current medications?'),
    ('doctor', 'No, continue your hypertension medication as prescribed. We will re-evaluate after the biopsy results. I\'ll send you a referral letter shortly.'),
]

msg_docs = []
for i, (role, content) in enumerate(messages):
    sender_id = str(patient_id) if role == 'patient' else str(doctor_id)
    msg_docs.append({
        'room_id': str(room_id),
        'sender_id': sender_id,
        'sender_role': role,
        'content': content,
        'timestamp': datetime.utcnow() - timedelta(days=5, minutes=len(messages) - i),
        'read': True,
    })
db.messages.insert_many(msg_docs)

print(f"✓ Created demo chat room with {len(messages)} messages")

# ─── Create consultation record ───────────────────────────────────────────────
db.consultations.insert_one({
    'patient_id': str(patient_id),
    'doctor_id': str(doctor_id),
    'status': 'active',
    'payment_status': 'paid',
    'amount': 5,
    'currency': 'INR',
    'requested_at': datetime.utcnow() - timedelta(days=5),
})
print("✓ Created consultation record (₹5)")

# ─── Summary ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 50)
print("✅ Database seeded successfully!")
print("\n📋 Demo Credentials:")
print("  Patient: patient@demo.com / demo1234")
print("  Doctor:  doctor@demo.com  / demo1234")
print("\nSkip email verification — accounts are pre-verified.")
print("=" * 50 + "\n")
