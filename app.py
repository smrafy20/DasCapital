from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DECIMAL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from decimal import Decimal

app = Flask(__name__)

# Load configuration
try:
    from config import Config
    app.config.from_object(Config)
except ImportError:
    # Fallback configuration if config.py doesn't exist
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/dashcapital'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'native' or 'foreign'
    balance = db.Column(DECIMAL(10, 2), default=100.00, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sent_requests = db.relationship('MoneyRequest', foreign_keys='MoneyRequest.sender_id', backref='sender', lazy='dynamic')
    received_requests = db.relationship('MoneyRequest', foreign_keys='MoneyRequest.recipient_id', backref='recipient', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.name} ({self.phone_number})>'
    
    def classify_user_type(self):
        """Classify user as native or foreign based on phone number"""
        if self.phone_number.startswith('+8801'):
            return 'native'
        return 'foreign'
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class MoneyRequest(db.Model):
    __tablename__ = 'money_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(DECIMAL(10, 2), nullable=False)
    note = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'accepted', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<MoneyRequest {self.amount} from {self.sender_id} to {self.recipient_id}>'

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'credit', 'debit'
    amount = db.Column(DECIMAL(10, 2), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('money_requests.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='transactions')
    money_request = db.relationship('MoneyRequest', backref='transactions')
    
    def __repr__(self):
        return f'<Transaction {self.transaction_type} {self.amount} for user {self.user_id}>'

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        phone_number = request.form['phone_number'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Basic validation
        if not all([name, phone_number, email, password]):
            flash('All fields are required!', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('register.html')

        # Check if user already exists
        if User.query.filter_by(phone_number=phone_number).first():
            flash('Phone number already registered!', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return render_template('register.html')

        # Create new user
        user = User(
            name=name,
            phone_number=phone_number,
            email=email,
            password_hash=generate_password_hash(password),
            user_type='native' if phone_number.startswith('+8801') else 'foreign',
            balance=Decimal('100.00')
        )

        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone_number = request.form['phone_number'].strip()
        password = request.form['password']

        if not phone_number or not password:
            flash('Phone number and password are required!', 'error')
            return render_template('login.html')

        user = User.query.filter_by(phone_number=phone_number).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid phone number or password!', 'error')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    # Get pending money requests (received)
    pending_requests = MoneyRequest.query.filter_by(
        recipient_id=user.id,
        status='pending'
    ).order_by(MoneyRequest.created_at.desc()).all()

    # Get recent transactions
    recent_transactions = Transaction.query.filter_by(
        user_id=user.id
    ).order_by(Transaction.created_at.desc()).limit(5).all()

    # Get sent requests status
    sent_requests = MoneyRequest.query.filter_by(
        sender_id=user.id
    ).order_by(MoneyRequest.created_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                         user=user,
                         pending_requests=pending_requests,
                         recent_transactions=recent_transactions,
                         sent_requests=sent_requests)

@app.route('/dashboard_data')
def dashboard_data():
    """Optimized API endpoint for dashboard data updates"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    user_id = session['user_id']

    # Single optimized query to get user with balance
    user = db.session.query(User.balance).filter_by(id=user_id).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    # Only get pending requests count and essential data
    pending_count = MoneyRequest.query.filter_by(
        recipient_id=user_id,
        status='pending'
    ).count()

    # If there are pending requests, get the details
    pending_requests_data = []
    if pending_count > 0:
        pending_requests = db.session.query(
            MoneyRequest.id,
            MoneyRequest.amount,
            MoneyRequest.note,
            MoneyRequest.created_at,
            User.name.label('sender_name'),
            User.phone_number.label('sender_phone')
        ).join(User, MoneyRequest.sender_id == User.id).filter(
            MoneyRequest.recipient_id == user_id,
            MoneyRequest.status == 'pending'
        ).order_by(MoneyRequest.created_at.desc()).all()

        pending_requests_data = [{
            'id': req.id,
            'sender_name': req.sender_name,
            'sender_phone': req.sender_phone,
            'amount': float(req.amount),
            'note': req.note,
            'created_at': req.created_at.strftime('%B %d, %Y at %I:%M %p')
        } for req in pending_requests]

    # Get recent sent requests (limited query)
    sent_requests = db.session.query(
        MoneyRequest.id,
        MoneyRequest.amount,
        MoneyRequest.status,
        MoneyRequest.created_at,
        User.name.label('recipient_name')
    ).join(User, MoneyRequest.recipient_id == User.id).filter(
        MoneyRequest.sender_id == user_id
    ).order_by(MoneyRequest.created_at.desc()).limit(3).all()

    sent_requests_data = [{
        'id': req.id,
        'recipient_name': req.recipient_name,
        'amount': float(req.amount),
        'status': req.status,
        'created_at': req.created_at.strftime('%b %d, %Y')
    } for req in sent_requests]

    # Get recent transactions (limited query)
    recent_transactions = Transaction.query.filter_by(
        user_id=user_id
    ).order_by(Transaction.created_at.desc()).limit(3).all()

    recent_transactions_data = [{
        'id': trans.id,
        'description': trans.description,
        'amount': float(trans.amount),
        'transaction_type': trans.transaction_type,
        'created_at': trans.created_at.strftime('%b %d, %Y at %I:%M %p')
    } for trans in recent_transactions]

    return jsonify({
        'success': True,
        'balance': float(user.balance),
        'pending_requests': pending_requests_data,
        'sent_requests': sent_requests_data,
        'recent_transactions': recent_transactions_data
    })

@app.route('/send_request', methods=['GET', 'POST'])
def send_request():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    if request.method == 'POST':
        recipient_id = request.form.get('recipient_id')
        amount = request.form.get('amount')
        note = request.form.get('note', '').strip()

        # Validation
        if not recipient_id or not amount:
            flash('Please select a recipient and enter an amount.', 'error')
            return render_template('send_request.html', user=user)

        try:
            amount = Decimal(amount)
            if amount <= 0:
                flash('Amount must be greater than 0.', 'error')
                return render_template('send_request.html', user=user)
        except:
            flash('Please enter a valid amount.', 'error')
            return render_template('send_request.html', user=user)

        recipient = User.query.get(recipient_id)
        if not recipient:
            flash('Selected recipient not found.', 'error')
            return render_template('send_request.html', user=user)

        if recipient.id == user.id:
            flash('You cannot send a request to yourself.', 'error')
            return render_template('send_request.html', user=user)

        # Create money request
        money_request = MoneyRequest(
            sender_id=user.id,
            recipient_id=recipient.id,
            amount=amount,
            note=note
        )

        try:
            db.session.add(money_request)
            db.session.commit()

            # Check if it's an AJAX request
            if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                return f'Money request sent to {recipient.name} successfully!'
            else:
                flash(f'Money request sent to {recipient.name} successfully!', 'success')
                return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()

            # Check if it's an AJAX request
            if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                return 'Failed to send money request. Please try again.'
            else:
                flash('Failed to send money request. Please try again.', 'error')

    return render_template('send_request.html', user=user)

@app.route('/search_users')
def search_users():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({'users': []})

    current_user_id = session['user_id']
    users = User.query.filter(
        User.id != current_user_id,
        User.name.ilike(f'%{query}%')
    ).limit(10).all()

    user_list = [{
        'id': user.id,
        'name': user.name,
        'phone_number': user.phone_number,
        'user_type': user.user_type
    } for user in users]

    return jsonify({'users': user_list})

@app.route('/process_request', methods=['POST'])
def process_request():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    data = request.get_json()
    request_id = data.get('request_id')
    action = data.get('action')  # 'accept' or 'reject'

    if not request_id or action not in ['accept', 'reject']:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400

    user = User.query.get(session['user_id'])
    money_request = MoneyRequest.query.get(request_id)

    if not money_request or money_request.recipient_id != user.id:
        return jsonify({'success': False, 'message': 'Request not found'}), 404

    if money_request.status != 'pending':
        return jsonify({'success': False, 'message': 'Request already processed'}), 400

    try:
        if action == 'accept':
            # Check if recipient has sufficient balance
            if user.balance < money_request.amount:
                return jsonify({'success': False, 'message': 'Insufficient balance'}), 400

            # Transfer money
            user.balance -= money_request.amount
            sender = User.query.get(money_request.sender_id)
            sender.balance += money_request.amount

            # Create transaction records
            recipient_transaction = Transaction(
                user_id=user.id,
                transaction_type='debit',
                amount=money_request.amount,
                description=f'Money sent to {sender.name}',
                request_id=money_request.id
            )

            sender_transaction = Transaction(
                user_id=sender.id,
                transaction_type='credit',
                amount=money_request.amount,
                description=f'Money received from {user.name}',
                request_id=money_request.id
            )

            db.session.add(recipient_transaction)
            db.session.add(sender_transaction)

        # Update request status
        money_request.status = action + 'ed'  # 'accepted' or 'rejected'
        money_request.processed_at = datetime.utcnow()

        db.session.commit()

        message = f'Request {action}ed successfully'
        if action == 'accept':
            message += f'. ৳{money_request.amount} transferred to {sender.name}.'

        return jsonify({'success': True, 'message': message})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while processing the request'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
