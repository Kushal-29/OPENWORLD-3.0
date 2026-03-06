import logging
import os
import sys
import traceback
from datetime import datetime

from flask import Flask, redirect, jsonify, render_template, request, url_for
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO
from dotenv import load_dotenv
from sqlalchemy.pool import QueuePool

# =====================================================
# LOAD ENV
# =====================================================
load_dotenv()

# =====================================================
# LOGGING
# =====================================================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("openworld")

logger.info("=================================================")
logger.info("OPENWORLD STARTING")
logger.info("=================================================")

# =====================================================
# IMPORT CONFIG + MODELS
# =====================================================
try:
    from config import config
    from models.models import db, User
except Exception as e:
    logger.error("Failed loading config/models")
    traceback.print_exc()
    sys.exit(1)

# =====================================================
# CREATE FLASK APP
# =====================================================
app = Flask(__name__)
app.config.from_object(config)

# =====================================================
# DATABASE CONFIG - WITH CONNECTION POOLING
# =====================================================
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # ✅ IMPROVED: Use connection pooling for PostgreSQL
    # Replace sqlite:// with postgresql+psycopg2://
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "poolclass": QueuePool,
        "pool_size": 10,
        "pool_recycle": 3600,  # Recycle connections every hour
        "pool_pre_ping": True,  # Test connections before using them
        "max_overflow": 20,
    }
    logger.info("✅ Using PostgreSQL with connection pooling")
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    logger.warning("⚠️  Using SQLite (dev mode only)")

db.init_app(app)

# =====================================================
# SOCKET.IO - PRODUCTION SETTINGS
# =====================================================
# ✅ CRITICAL FIX: Changed async_mode from "eventlet" to "threading"
# Reason: eventlet 0.36.1 has compatibility issues with Flask-SocketIO 5.3.4
# threading mode is more stable and reliable
socketio = SocketIO(
    app,
    cors_allowed_origins=[
        "https://theopenworld.in",
        "http://theopenworld.in",
        "https://www.theopenworld.in",
        "http://www.theopenworld.in",
    ],
    async_mode="threading",   # ✅ FIXED: Changed from "eventlet"
    ping_timeout=120,
    ping_interval=25,
    max_http_buffer_size=1e6,
    logger=True,
    engineio_logger=True
)

logger.info("✅ SocketIO initialized with production settings (threading mode)")

# =====================================================
# LOGIN MANAGER
# =====================================================
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"User load error: {e}")
        return None


logger.info("✅ LoginManager configured")

# =====================================================
# REGISTER BLUEPRINTS
# =====================================================
try:
    from routes.auth import auth_bp
    from routes.profile import profile_bp
    from routes.chat import chat_bp
    from routes.match import match_bp
    from routes.api import api_bp
    from routes.friend_requests import friend_requests_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(match_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(friend_requests_bp)

    logger.info("✅ All blueprints registered")

except Exception:
    logger.error("❌ Blueprint loading failed")
    traceback.print_exc()

# =====================================================
# SOCKET EVENTS
# =====================================================
try:
    from socketio_events.match_events import init_match_events
    from socketio_events.chat_events import init_chat_events
    from socketio_events.friend_events import init_friend_events

    init_match_events(socketio)
    init_chat_events(socketio)
    init_friend_events(socketio)

    logger.info("✅ Socket events registered")

except Exception:
    logger.error("❌ Socket events failed")
    traceback.print_exc()

# =====================================================
# ROUTES
# =====================================================

@app.route("/", endpoint="root")
def root():
    """
    Main entry route
    """
    try:
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        return redirect(url_for("auth.login"))
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "root failed"}), 500


@app.route("/home", endpoint="home")
def home():
    """
    User dashboard
    """
    try:
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        return render_template(
            "home.html",
            user=current_user
        )

    except Exception:
        traceback.print_exc()
        return jsonify({"error": "home failed"}), 500


# =====================================================
# HEALTH CHECKS
# =====================================================

@app.route("/health")
def health():
    try:
        # ✅ IMPROVED: Test database connection
        user_count = User.query.count()
        return jsonify({
            "status": "ok",
            "service": "openworld",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "error",
            "service": "openworld",
            "database": "disconnected",
            "error": str(e)
        }), 503


@app.route("/api/health")
def api_health():
    try:
        user_count = User.query.count()
        return jsonify({
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "openworld",
            "database": "connected"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 503


logger.info("✅ Routes initialized")

# =====================================================
# ERROR HANDLERS
# =====================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "error": "not_found",
        "path": request.path
    }), 404


@app.errorhandler(500)
def server_error(e):
    traceback.print_exc()
    logger.error(f"Server error: {e}")
    return jsonify({
        "error": "internal_error",
        "message": str(e) if app.debug else "Internal server error"
    }), 500


# =====================================================
# REQUEST CONTEXT ERROR HANDLING
# =====================================================

@app.before_request
def before_request():
    """
    ✅ IMPROVED: Log all requests for debugging
    """
    logger.info(f"{request.method} {request.path}")


@app.after_request
def after_request(response):
    """
    ✅ IMPROVED: Add security headers
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


# =====================================================
# LOCAL DEVELOPMENT ONLY
# =====================================================
if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
            logger.info("✅ Database tables created")
        except Exception as e:
            logger.error(f"Database creation failed: {e}")
    
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_ENV") == "development"
    )