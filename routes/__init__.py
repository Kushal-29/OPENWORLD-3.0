from flask import Blueprint

# Import all blueprints
from .auth import auth_bp
from .match import match_bp
from .chat import chat_bp
from .profile import profile_bp
from .api import api_bp

__all__ = [
    'auth_bp',
    'match_bp', 
    'chat_bp',
    'profile_bp',
    'api_bp'
]