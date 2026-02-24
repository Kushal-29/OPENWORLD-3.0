import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_ECHO = False
    
    # File uploads
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')
    UPLOAD_CHAT = os.path.join(os.getcwd(), 'static/uploads/chat')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
    
    # Session
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Logic to build URI from .env or fallback to local SQLite
    _DB_USER = os.getenv('DB_USER')
    _DB_PASS = os.getenv('DB_PASSWORD')
    _DB_HOST = os.getenv('DB_HOST', 'localhost')
    _DB_PORT = os.getenv('DB_PORT', '5432')
    _DB_NAME = os.getenv('DB_NAME')

    if all([_DB_USER, _DB_PASS, _DB_NAME]):
        SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{_DB_USER}:{_DB_PASS}@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}"
    else:
        # Fallback to SQLite if Postgres info is missing to prevent RuntimeError
        SQLALCHEMY_DATABASE_URI = 'sqlite:///dev_fallback.db'
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = 86400

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Select config based on environment
config_name = os.getenv('FLASK_ENV', 'development')
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

# IMPORTANT: We instantiate the class with () so app.config.from_object(config) works perfectly
config = config_dict.get(config_name, DevelopmentConfig)()