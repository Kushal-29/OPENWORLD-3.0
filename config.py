import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False
    SOCKETIO_CORS_ALLOWED_ORIGINS = [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:3000",
        "*"  # Allow all for development
    ]

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    SOCKETIO_CORS_ALLOWED_ORIGINS = [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "*"
    ]

class ProductionConfig(Config):
    """Production configuration for Railway/Heroku"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True
    
    # ===== SOCKET.IO CORS CONFIGURATION (MOBILE FRIENDLY) =====
    # FIXED: Better handling of mobile CORS
    cors_origins_str = os.getenv('SOCKETIO_CORS_ALLOWED_ORIGINS', '')
    
    if cors_origins_str:
        # If environment variable is set, use it
        SOCKETIO_CORS_ALLOWED_ORIGINS = [
            origin.strip() for origin in cors_origins_str.split(',')
        ]
    else:
        # Default CORS origins for production
        # FIXED: Added more combinations for mobile browsers and different protocols
        SOCKETIO_CORS_ALLOWED_ORIGINS = [
            # Main domain - HTTP
            "http://theopenworld.in",
            "http://www.theopenworld.in",
            # Main domain - HTTPS (preferred)
            "https://theopenworld.in",
            "https://www.theopenworld.in",
            # Mobile-specific variations
            "http://theopenworld.in:80",
            "https://theopenworld.in:443",
            "http://www.theopenworld.in:80",
            "https://www.theopenworld.in:443",
            # Without www
            "theopenworld.in",
            "www.theopenworld.in",
        ]

# Select configuration based on environment
config_name = os.getenv('FLASK_ENV', 'development')

if config_name == 'production':
    config = ProductionConfig
elif config_name == 'testing':
    config = TestingConfig
else:
    config = DevelopmentConfig

# Log the configuration being used (helpful for debugging)
import logging
logger = logging.getLogger(__name__)
logger.info("Using config: " + config_name)