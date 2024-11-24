from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .models import db, User

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Define user_loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .api import api_bp
    from .routes import api_bp as routes_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(routes_bp)

    return app
