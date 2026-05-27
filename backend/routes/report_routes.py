"""routes/report_routes.py"""
from flask import Blueprint
from controllers.report_controller import generate_report, list_reports

report_bp = Blueprint('reports', __name__)
report_bp.route('/', methods=['GET'])(list_reports)
report_bp.route('/download/<prediction_id>', methods=['GET'])(generate_report)
