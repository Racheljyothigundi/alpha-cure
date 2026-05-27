"""routes/doctor_routes.py"""
from flask import Blueprint
from controllers.doctor_controller import (
    get_all_doctors, get_cancer_patients, get_doctor_stats,
    create_consultation_order, verify_consultation_payment, get_consultations
)

doctor_bp = Blueprint('doctor', __name__)
doctor_bp.route('/list', methods=['GET'])(get_all_doctors)
doctor_bp.route('/patients', methods=['GET'])(get_cancer_patients)
doctor_bp.route('/stats', methods=['GET'])(get_doctor_stats)
doctor_bp.route('/consultation/create-order', methods=['POST'])(create_consultation_order)
doctor_bp.route('/consultation/verify-payment', methods=['POST'])(verify_consultation_payment)
doctor_bp.route('/consultation/list', methods=['GET'])(get_consultations)
