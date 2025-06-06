# app/__init__.py

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    load_dotenv()

    # CONFIG
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev_secret")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate = Migrate(app, db)

    print(f"[DEBUG] DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # REGISTER MODELS
    from .models import User, FileMetadata

    # REGISTER BLUEPRINTS
    from .auth import auth as auth_bp
    app.register_blueprint(auth_bp)

    from .routes import main as main_bp
    app.register_blueprint(main_bp)

    return app
