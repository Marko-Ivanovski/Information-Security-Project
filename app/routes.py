# app/routes.py

from flask import Blueprint, render_template, g, redirect, url_for
from .auth import login_required

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if g.user:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    username = g.user.username
    files = g.user.files

    return render_template(
        'dashboard.html',
        username=username,
        files=files
    )
