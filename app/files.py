# app/files.py

import os
import hashlib
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, send_from_directory, current_app, g, abort
)
from werkzeug.utils import secure_filename
from uuid import uuid4
from . import db
from .models import FileMetadata
from .auth import login_required

files = Blueprint('files', __name__)

def allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']

@files.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        f = request.files.get('file')
        if not f or f.filename == '':
            flash('No file selected.')
            return redirect(url_for('files.upload'))

        if not allowed_file(f.filename):
            flash('File type not allowed.')
            return redirect(url_for('files.upload'))

        original = secure_filename(f.filename)
        data = f.read()
        sha256 = hashlib.sha256(data).hexdigest()
        f.stream.seek(0)
        is_public = (request.form.get('visibility') == 'public')

        # Create metadata (this sets stored_filename = uuid4().hex)
        meta = FileMetadata(
            owner_id=g.user.id,
            original_filename=original,
            sha256_hash=sha256,
            description=None,
            is_public=is_public
        )
        db.session.add(meta)
        db.session.commit()

        # Save to disk under UPLOAD_FOLDER
        dest = os.path.join(current_app.config['UPLOAD_FOLDER'], meta.stored_filename)
        f.save(dest)

        flash('Upload successful.')
        return redirect(url_for('main.dashboard'))

    return render_template('upload.html')

@files.route('/download/<int:file_id>')
def download(file_id):
    meta = FileMetadata.query.get_or_404(file_id)

    if meta.is_public:
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            meta.stored_filename,
            as_attachment=True,
            download_name=meta.original_filename
        )

    if not g.user:
        return redirect(url_for('auth.login'))

    if meta.owner_id != g.user.id:
        abort(403)

    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        meta.stored_filename,
        as_attachment=True,
        download_name=meta.original_filename
    )

@files.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete(file_id):
    meta = FileMetadata.query.get_or_404(file_id)
    if meta.owner_id != g.user.id:
        abort(403)

    # Remove file from disk
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], meta.stored_filename)
    if os.path.exists(path):
        os.remove(path)

    db.session.delete(meta)
    db.session.commit()
    flash('File deleted.')
    return redirect(url_for('main.dashboard'))
