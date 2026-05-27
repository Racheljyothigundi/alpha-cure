"""routes/hospital_routes.py"""
from flask import Blueprint
from controllers.hospital_controller import get_nearby_hospitals

hospital_bp = Blueprint('hospitals', __name__)
hospital_bp.route('/nearby', methods=['GET'])(get_nearby_hospitals)
