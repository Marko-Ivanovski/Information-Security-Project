# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev_secret")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .models import User, FileMetadata

    # (Optional) import and register blueprints here
    # from .auth import auth_bp
    # app.register_blueprint(auth_bp)

    return app

