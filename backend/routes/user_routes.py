"""routes/user_routes.py"""
from flask import Blueprint
from controllers.user_controller import get_profile, update_profile, get_dashboard_stats

user_bp = Blueprint('user', __name__)
user_bp.route('/profile', methods=['GET'])(get_profile)
user_bp.route('/profile', methods=['PUT'])(update_profile)
user_bp.route('/dashboard', methods=['GET'])(get_dashboard_stats)
