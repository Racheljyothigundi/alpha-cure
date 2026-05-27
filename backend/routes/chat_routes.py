"""routes/chat_routes.py"""
from flask import Blueprint
from controllers.chat_controller import get_messages, get_chat_rooms, create_room, ai_chatbot

chat_bp = Blueprint('chat', __name__)
chat_bp.route('/rooms', methods=['GET'])(get_chat_rooms)
chat_bp.route('/rooms', methods=['POST'])(create_room)
chat_bp.route('/messages/<room_id>', methods=['GET'])(get_messages)
chat_bp.route('/ai', methods=['POST'])(ai_chatbot)
