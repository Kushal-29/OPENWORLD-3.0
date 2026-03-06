from .match_events import init_match_events
from .chat_events import init_chat_events

def init_socket_events(socketio):
    """Initialize all Socket.IO events"""
    init_match_events(socketio)
    init_chat_events(socketio)