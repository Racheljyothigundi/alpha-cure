"""
Alpha-Cure Backend - Flask Application Entry Point
"""

import os
import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv

from utils.db import init_db
from utils.error_handlers import register_error_handlers
from model_selector import load_model
from services.image_model_service import preload_image_models

# ─── Load environment ───────────────────────────────────────────────────────────
load_dotenv()

# ─── Initialize Flask ───────────────────────────────────────────────────────────
app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', 'alpha-cure-secret')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

allowed_origins = [
    'http://localhost:3000',
    'https://alpha-cure-frontend.vercel.app',
]
frontend_url = os.getenv('FRONTEND_URL')
if frontend_url and frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)

CORS(
    app,
    resources={r"/api/*": {"origins": allowed_origins}},
    supports_credentials=True,
)

# ─── Socket.IO ─────────────────────────────────────────────────────────────────
socketio = SocketIO(
    app,
    cors_allowed_origins=allowed_origins,
    async_mode='eventlet',
    logger=False,
    engineio_logger=False
)

# ─── Register Blueprints ────────────────────────────────────────────────────────
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.prediction_routes import prediction_bp
from routes.report_routes import report_bp
from routes.chat_routes import chat_bp
from routes.hospital_routes import hospital_bp
from routes.doctor_routes import doctor_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(prediction_bp, url_prefix='/api')
app.register_blueprint(report_bp, url_prefix='/api/reports')
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(hospital_bp, url_prefix='/api/hospitals')
app.register_blueprint(doctor_bp, url_prefix='/api/doctor')

# ─── Socket.IO Events ──────────────────────────────────────────────────────────
from services.socket_service import register_socket_events
register_socket_events(socketio)
register_error_handlers(app)

_startup_complete = False


def initialize_services():
    global _startup_complete

    if _startup_complete:
        return

    init_db()
    load_model()
    preload_image_models()
    _startup_complete = True


initialize_services()

# ─── Health Check ───────────────────────────────────────────────────────────────
@app.route('/api/health')
def health():
    return {'status': 'ok', 'service': 'Alpha-Cure API', 'version': '1.0.0'}

# ─── Startup ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\n🔬 Alpha-Cure Backend starting on http://localhost:5000\n")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
