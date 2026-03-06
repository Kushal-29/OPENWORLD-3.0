import logging

logging.basicConfig(level=logging.INFO)

logging.info("============================================================")
logging.info("OPENWORLD WSGI - Production Mode Startup")
logging.info("============================================================")

logging.info("Importing Flask app and SocketIO...")

from app import app, socketio

logging.info("✅ Flask app and SocketIO imported successfully")

# Gunicorn entrypoint
application = app

logging.info("✅ WSGI app ready for gunicorn")
logging.info("============================================================")