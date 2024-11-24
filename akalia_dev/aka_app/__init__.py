from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# Initialize extensions
db = SQLAlchemy()
socketio = SocketIO()  # Initialize SocketIO

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app)  # Bind SocketIO to the Flask app

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    from .api import api_bp
    from .routes import api_bp as routes_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(routes_bp)

    return app
