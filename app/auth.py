# app/auth.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User
from functools import wraps

auth = Blueprint('auth', __name__)

@auth.before_app_request
def load_logged_in_user():
    """
    If user_id is in session, load the full User into `g.user`.
    Otherwise, set g.user = None.
    This lets you check `g.user` in any view template or route.
    """
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)

def login_required(view_func):
    """
    Simple decorator to ensure that a route can only be accessed
    if g.user is not None (i.e. someone is logged in).
    """
    @wraps(view_func)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view_func(**kwargs)
    return wrapped_view

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    GET  → show the registration form
    POST → process username/password, create new User
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Basic validation
        if not username or not password:
            flash('Please provide both username and password.')
            return redirect(url_for('auth.register'))

        # Check if that username already exists
        existing = User.query.filter_by(username=username).first()
        if existing:
            flash('Username already taken.')
            return redirect(url_for('auth.register'))

        # Create new user with a hashed password
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.')
        return redirect(url_for('auth.login'))

    # If GET, just show the form
    return render_template('register.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  → show the login form
    POST → verify credentials, set session['user_id']
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Find user by username
        user = User.query.filter_by(username=username).first()

        # If user not found or password doesn’t match:
        if user is None or not check_password_hash(user.password_hash, password):
            flash('Invalid username or password.')
            return redirect(url_for('auth.login'))

        # Success: store user.id in session
        session.clear()
        session['user_id'] = user.id
        return redirect(url_for('main.dashboard'))

    return render_template('login.html')


@auth.route('/logout')
def logout():
    """Pop session and redirect to login."""
    session.clear()
    return redirect(url_for('auth.login'))
