from flask import Flask, render_template, redirect
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO
from dotenv import load_dotenv
import socket
import logging
from logging.handlers import RotatingFileHandler
import os

from config import config
from models.models import db, User

load_dotenv()

# Setup logging
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/openworld.log', maxBytes=10240000, backupCount=10)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))

# ======================
# HELPERS
# ======================
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# ======================
# APP INIT
# ======================
app = Flask(__name__)
app.config.from_object(config)

app.logger.addHandler(file_handler)
app.logger.setLevel(logging.DEBUG)

# ======================
# EXTENSIONS
# ======================
db.init_app(app)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    manage_session=False,
    ping_timeout=60,
    ping_interval=25,
    logger=True,
    engineio_logger=True
)

login_manager = LoginManager(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None

# ======================
# BLUEPRINTS
# ======================
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
    app.logger.info("✅ All blueprints registered")
except Exception as e:
    app.logger.error(f"❌ Blueprint error: {e}")

# ======================
# DB INIT
# ======================
with app.app_context():
    db.create_all()
    app.logger.info("✅ Database initialized")

# ======================
# SOCKET EVENTS
# ======================
try:
    from socketio_events.match_events import init_match_events
    from socketio_events.chat_events import init_chat_events
    from socketio_events.friend_events import init_friend_events

    init_match_events(socketio)
    init_chat_events(socketio)
    init_friend_events(socketio)
    app.logger.info("✅ All socket events registered")
except Exception as e:
    app.logger.error(f"❌ Socket event error: {e}")
    import traceback
    traceback.print_exc()

# ======================
# ERROR HANDLERS
# ======================
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    app.logger.error(f'❌ Server error: {error}')
    return render_template('500.html'), 500

# ======================
# BEFORE REQUEST
# ======================
@app.before_request
def before_request():
    if current_user.is_authenticated:
        from datetime import datetime
        current_user.last_seen = datetime.utcnow()
        try:
            db.session.commit()
        except:
            db.session.rollback()

# ======================
# ROUTES
# ======================
@app.route("/")
@app.route("/home")
def home():
    if current_user.is_authenticated:
        return render_template("home.html", user=current_user)
    return redirect("/login")

@app.route("/health")
def health():
    return {'status': 'ok'}, 200

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    local_ip = get_local_ip()

    print("\n" + "="*50)
    print("🚀 OPENWORLD VIDEO CHAT")
    print("="*50)
    print(f"Local:   http://localhost:5000")
    print(f"Network: http://{local_ip}:5000")
    print("="*50 + "\n")

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )