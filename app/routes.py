# app/routes.py

from flask import Blueprint, render_template, g, redirect, url_for
from .auth import login_required

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # If already logged in, go to dashboard; otherwise send to /login
    if g.user:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=g.user.username)
