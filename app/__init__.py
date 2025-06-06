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

    # ─── CONFIG ────────────────────────────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev_secret")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ─── FILE UPLOAD CONFIG ───────────────────────────────────────────────────
    # Support both UPLOAD_FOLDER or legacy FILE_STORAGE_PATH
    upload_folder = os.environ.get('UPLOAD_FOLDER') or os.environ.get('FILE_STORAGE_PATH')
    app.config['UPLOAD_FOLDER'] = upload_folder
    # Max upload size in bytes (0 = no limit)
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 0))
    # e.g. ".txt,.pdf"
    exts = os.environ.get('ALLOWED_EXTENSIONS', '')
    app.config['ALLOWED_EXTENSIONS'] = {
        x.strip().lower() for x in exts.split(',') if x.strip()
    }

    # ─── INITIALIZE EXTENSIONS ──────────────────────────────────────────────────
    db.init_app(app)
    Migrate(app, db)

    print(f"[DEBUG] DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"[DEBUG] Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"[DEBUG] Allowed extensions: {app.config['ALLOWED_EXTENSIONS']}")

    # ─── REGISTER MODELS ───────────────────────────────────────────────────────
    from .models import User, FileMetadata

    # ─── REGISTER BLUEPRINTS ───────────────────────────────────────────────────
    from .auth import auth as auth_bp
    app.register_blueprint(auth_bp)

    from .routes import main as main_bp
    app.register_blueprint(main_bp)

    from .files import files as files_bp
    app.register_blueprint(files_bp)

    return app
