from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import User
from db import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        pin = request.form['pin']

        user = User.query.filter_by(phone=phone, pin=pin).first()

        if user:
            session['user_id'] = user.id
            session['user_name'] = f"{user.first_name} {user.last_name}"
            flash(f"Welcome back, {session['user_name']}!")
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash("Invalid credentials")
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('auth.login'))

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        email = request.form['email']
        phone = request.form['phone']
        nid = request.form['nid']
        password = request.form['password']
        dob = request.form['dob']

        existing_user = User.query.filter(
            (User.phone == phone) | (User.email == email)
        ).first()
        if existing_user:
            flash("User with this phone or email already exists.")
            return redirect(url_for('auth.signup'))

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            nid=nid,
            pin=password,
            dob=dob,
            balance=0,
            full_name=f"{first_name} {last_name}"
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! Please login.")
        return redirect(url_for('auth.login'))

    return render_template('signup.html')
