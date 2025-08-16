from db import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    nid = db.Column(db.String(20), nullable=False, unique=True)
    pin = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)

    transactions = db.relationship('Transaction', backref='user', lazy=True)

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    trx_id = db.Column(db.String(50), nullable=False, unique=True)
    type = db.Column(db.String(10), nullable=False)  # 'add' or 'send'
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50), nullable=False)
    source_dest = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
