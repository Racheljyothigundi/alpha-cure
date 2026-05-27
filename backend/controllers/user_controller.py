"""controllers/user_controller.py"""

from flask import request, jsonify
from bson import ObjectId
from datetime import datetime

from utils.db import get_db
from utils.jwt_utils import token_required


@token_required
def get_profile():
    db = get_db()
    user = db.users.find_one({'_id': ObjectId(request.user_id)}, {'password': 0})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user['_id'] = str(user['_id'])
    if 'created_at' in user:
        user['created_at'] = user['created_at'].isoformat()

    return jsonify({'user': user}), 200


@token_required
def update_profile():
    data = request.get_json()
    allowed = ['name', 'phone', 'profile', 'specialization']
    update_data = {k: v for k, v in data.items() if k in allowed}
    update_data['updated_at'] = datetime.utcnow()

    db = get_db()
    db.users.update_one({'_id': ObjectId(request.user_id)}, {'$set': update_data})
    return jsonify({'message': 'Profile updated successfully'}), 200


@token_required
def get_dashboard_stats():
    db = get_db()
    user_id = ObjectId(request.user_id)

    predictions = list(db.predictions.find({'user_id': user_id}, sort=[('timestamp', -1)], limit=5))
    for p in predictions:
        p['_id'] = str(p['_id'])
        p['user_id'] = str(p['user_id'])
        p['timestamp'] = p['timestamp'].isoformat()

    total_preds = db.predictions.count_documents({'user_id': user_id})
    high_risk = db.predictions.count_documents({'user_id': user_id, 'risk_level': {'$in': ['HIGH', 'CRITICAL']}})

    return jsonify({
        'total_predictions': total_preds,
        'high_risk_count': high_risk,
        'recent_predictions': predictions,
    }), 200
