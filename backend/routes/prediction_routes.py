"""routes/prediction_routes.py"""
from flask import Blueprint
from controllers.prediction_controller import (
    predict_cancer,
    predict_cancer_image,
    get_image_models,
    get_prediction_history,
)

prediction_bp = Blueprint('prediction', __name__)
prediction_bp.route('/predict', methods=['POST'])(predict_cancer)
prediction_bp.route('/predict-image', methods=['POST'])(predict_cancer_image)
prediction_bp.route('/image-models', methods=['GET'])(get_image_models)
prediction_bp.route('/predictions', methods=['GET'])(get_prediction_history)
