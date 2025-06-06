# app/routes.py

from flask import Blueprint, render_template, g, redirect, url_for
from .models import FileMetadata

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('main.dashboard'))

@main.route('/dashboard')
def dashboard():
    public_files = FileMetadata.query \
        .filter_by(is_public=True) \
        .order_by(FileMetadata.upload_timestamp.desc()) \
        .all()

    if g.user:
        private_files = [f for f in g.user.files if not f.is_public]
    else:
        private_files = []

    return render_template(
        'dashboard.html',
        username      = (g.user.username if g.user else None),
        public_files  = public_files,
        private_files = private_files
    )
