# app/models.py

from datetime import datetime
from uuid import uuid4

from flask_sqlalchemy import SQLAlchemy

# db = SQLAlchemy()
from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    public_value = db.Column(db.Text, nullable=False)
    # (Optionally) if you want to store an encryption key per user:
    # encryption_key = db.Column(db.String(44), nullable=True)

    # Relationship: one user → many files
    files = db.relationship("FileMetadata", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"


class FileMetadata(db.Model):
    __tablename__ = "file_metadata"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_filename = db.Column(db.String(256), nullable=False)
    stored_filename = db.Column(db.String(64), unique=True, nullable=False)
    upload_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sha256_hash = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Relationship back to User
    owner = db.relationship("User", back_populates="files")

    def __init__(self, owner_id, original_filename, sha256_hash, description=None):
        self.owner_id = owner_id
        self.original_filename = original_filename
        self.stored_filename = uuid4().hex
        self.sha256_hash = sha256_hash
        self.description = description

    def __repr__(self):
        return (
            f"<FileMetadata id={self.id} "
            f"owner_id={self.owner_id} original={self.original_filename} "
            f"stored={self.stored_filename}>"
        )
