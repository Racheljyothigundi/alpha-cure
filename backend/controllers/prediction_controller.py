"""controllers/prediction_controller.py"""

from flask import request, jsonify
from datetime import datetime
from bson import ObjectId
from werkzeug.utils import secure_filename

from utils.db import get_db
from utils.jwt_utils import role_required


@role_required('patient')
def predict_cancer():
    """
    POST /api/predict
    Accepts clinical features and returns AI cancer prediction.
    Features match the notebook training data (tabular, not image).
    """
    from model_selector import load_model, predict

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    # Extract clinical features (matches notebook dataset columns)
    features = {
        'age': float(data.get('age', 0)),
        'gender': float(data.get('gender', 0)),       # 0=Female, 1=Male
        'bmi': float(data.get('bmi', 22.0)),
        'smoking': float(data.get('smoking', 0)),      # 0=No, 1=Yes
        'genetic_risk': float(data.get('genetic_risk', 0)),   # 0=Low, 1=Med, 2=High
        'physical_activity': float(data.get('physical_activity', 3)),
        'alcohol_intake': float(data.get('alcohol_intake', 0)),
        'cancer_history': float(data.get('cancer_history', 0)),
        'diagnosis': float(data.get('diagnosis', 0)),  # 0=No prior, 1=Yes
    }

    load_model()
    result = predict(features)

    if not result.get('success'):
        return jsonify({'error': result.get('error', 'Prediction failed')}), 500

    # Save prediction to database
    db = get_db()
    pred_doc = {
        'user_id': ObjectId(request.user_id),
        'features': features,
        'prediction': result['prediction'],
        'label': result['label'],
        'code': result['code'],
        'confidence': result['confidence'],
        'risk_level': result['risk_level'],
        'probabilities': result['probabilities'],
        'suggestions': result['suggestions'],
        'timestamp': datetime.utcnow(),
    }
    inserted = db.predictions.insert_one(pred_doc)
    pred_doc['_id'] = str(inserted.inserted_id)

    # Update user prediction history
    db.users.update_one(
        {'_id': ObjectId(request.user_id)},
        {'$push': {'prediction_history': {
            'prediction_id': str(inserted.inserted_id),
            'label': result['label'],
            'confidence': result['confidence'],
            'risk_level': result['risk_level'],
            'date': datetime.utcnow()
        }}}
    )

    return jsonify({
        'success': True,
        'prediction_id': str(inserted.inserted_id),
        **result
    }), 200


@role_required('patient')
def predict_cancer_image():
    """
    POST /api/predict-image
    Accepts an uploaded image and runs the selected image screening model.
    """
    from services.image_model_service import predict_uploaded_image

    image_file = request.files.get('image')
    if image_file is None:
        return jsonify({'error': 'Please upload an image file.'}), 400

    model_key = (request.form.get('model_key') or 'skin_lesion').strip()

    filename = secure_filename(image_file.filename or 'skin-lesion-upload.jpg')
    if not filename:
        filename = 'skin-lesion-upload.jpg'

    image_bytes = image_file.read()
    if not image_bytes:
        return jsonify({'error': 'Uploaded image is empty.'}), 400

    try:
        result = predict_uploaded_image(
            image_bytes,
            model_key=model_key,
            filename=filename,
        )
    except KeyError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500

    db = get_db()
    pred_doc = {
        'user_id': ObjectId(request.user_id),
        'prediction_type': 'image',
        'model_key': model_key,
        'input_filename': filename,
        'label': result['label'],
        'code': result['code'],
        'prediction': result['prediction'],
        'confidence': result['confidence'],
        'risk_level': result['risk_level'],
        'probabilities': result['probabilities'],
        'suggestions': result['suggestions'],
        'model_name': result['model_name'],
        'note': result.get('note'),
        'timestamp': datetime.utcnow(),
    }
    inserted = db.predictions.insert_one(pred_doc)

    db.users.update_one(
        {'_id': ObjectId(request.user_id)},
        {'$push': {'prediction_history': {
            'prediction_id': str(inserted.inserted_id),
            'label': result['label'],
            'confidence': result['confidence'],
            'risk_level': result['risk_level'],
            'type': 'image',
            'date': datetime.utcnow()
        }}}
    )

    return jsonify({
        'success': True,
        'prediction_id': str(inserted.inserted_id),
        **result
    }), 200


@role_required('patient')
def get_image_models():
    """GET /api/image-models - Get available image screening models."""
    from services.image_model_service import list_image_screening_models

    return jsonify({'models': list_image_screening_models()}), 200


@role_required('patient')
def get_prediction_history():
    """GET /api/predictions - Get user's prediction history"""
    db = get_db()
    preds = list(db.predictions.find(
        {'user_id': ObjectId(request.user_id)},
        sort=[('timestamp', -1)],
        limit=20
    ))
    for p in preds:
        p['_id'] = str(p['_id'])
        p['user_id'] = str(p['user_id'])
        p['timestamp'] = p['timestamp'].isoformat()

    return jsonify({'predictions': preds}), 200
