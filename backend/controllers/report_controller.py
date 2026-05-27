"""controllers/report_controller.py - PDF report generation"""

import os
import io
from flask import request, jsonify, send_file
from bson import ObjectId
from datetime import datetime

from utils.db import get_db
from utils.jwt_utils import role_required

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

RISK_COLORS = {
    'LOW': '#16a34a',
    'MODERATE': '#d97706',
    'HIGH': '#dc2626',
    'CRITICAL': '#7c3aed',
}


@role_required('patient')
def generate_report(prediction_id):
    db = get_db()
    pred = db.predictions.find_one({
        '_id': ObjectId(prediction_id),
        'user_id': ObjectId(request.user_id)
    })
    if not pred:
        return jsonify({'error': 'Prediction not found'}), 404

    user = db.users.find_one({'_id': pred['user_id']}, {'password': 0})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not REPORTLAB_AVAILABLE:
        # Return JSON report as fallback
        return jsonify({
            'report': {
                'patient_name': user['name'],
                'email': user['email'],
                'role': 'Patient',
                'prediction': pred['label'],
                'confidence': pred['confidence'],
                'risk_level': pred['risk_level'],
                'suggestions': pred['suggestions'],
                'date': pred['timestamp'].isoformat(),
            }
        }), 200

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm,
                             leftMargin=20*mm, rightMargin=20*mm)

    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle('header', fontSize=24, fontName='Helvetica-Bold',
                                   textColor=colors.HexColor('#0284c7'), alignment=TA_CENTER)
    story.append(Paragraph("Alpha-Cure", header_style))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("AI-Powered Cancer Detection Report",
                           ParagraphStyle('sub', fontSize=14, textColor=colors.HexColor('#64748b'), alignment=TA_CENTER)))
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 6*mm))

    # Patient Info
    story.append(Paragraph("Patient Information", ParagraphStyle('h2', fontSize=14, fontName='Helvetica-Bold',
                                                                   textColor=colors.HexColor('#1e293b'))))
    story.append(Spacer(1, 4*mm))

    patient_data = [
        ['Patient Name:', user['name'], 'Report Date:', pred['timestamp'].strftime('%d %b %Y, %H:%M')],
        ['Email:', user['email'], 'Report ID:', str(pred['_id'])[:16] + '...'],
        ['Role:', 'Patient', '', ''],
    ]
    pt = Table(patient_data, colWidths=[45*mm, 65*mm, 35*mm, 50*mm])
    pt.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#334155')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(pt)
    story.append(Spacer(1, 6*mm))

    # Prediction Result
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("AI Prediction Result", ParagraphStyle('h2', fontSize=14, fontName='Helvetica-Bold',
                                                                    textColor=colors.HexColor('#1e293b'))))
    story.append(Spacer(1, 4*mm))

    risk_color = RISK_COLORS.get(pred['risk_level'], '#64748b')
    result_data = [
        ['Diagnosis:', pred['label']],
        ['Confidence Score:', f"{pred['confidence']}%"],
        ['Risk Level:', pred['risk_level']],
    ]
    rt = Table(result_data, colWidths=[60*mm, 120*mm])
    rt.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#334155')),
        ('TEXTCOLOR', (1, 2), (1, 2), colors.HexColor(risk_color)),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(rt)
    story.append(Spacer(1, 6*mm))

    # Suggestions
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("AI Recommendations", ParagraphStyle('h2', fontSize=14, fontName='Helvetica-Bold',
                                                                  textColor=colors.HexColor('#1e293b'))))
    story.append(Spacer(1, 4*mm))

    for i, sugg in enumerate(pred.get('suggestions', []), 1):
        story.append(Paragraph(f"{i}. {sugg}",
                               ParagraphStyle('bullet', fontSize=10, leftIndent=10,
                                              textColor=colors.HexColor('#475569'), spaceAfter=4)))

    # Disclaimer
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 4*mm))
    disclaimer = ("⚠️ DISCLAIMER: This report is generated by an AI model and is intended for "
                  "informational purposes only. It does not constitute medical advice. "
                  "Please consult a qualified healthcare professional for diagnosis and treatment.")
    story.append(Paragraph(disclaimer, ParagraphStyle('disc', fontSize=9, textColor=colors.HexColor('#94a3b8'),
                                                       alignment=TA_LEFT)))

    doc.build(story)
    buffer.seek(0)

    filename = f"AlphaCure_Report_{user['name'].replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return send_file(buffer, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)


@role_required('patient')
def list_reports():
    db = get_db()
    preds = list(db.predictions.find(
        {'user_id': ObjectId(request.user_id)},
        sort=[('timestamp', -1)]
    ))
    reports = []
    for p in preds:
        reports.append({
            'id': str(p['_id']),
            'label': p['label'],
            'confidence': p['confidence'],
            'risk_level': p['risk_level'],
            'date': p['timestamp'].isoformat(),
        })
    return jsonify({'reports': reports}), 200
