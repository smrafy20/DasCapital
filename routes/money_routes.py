from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import uuid
from db import db
from models import User, Transaction

money_bp = Blueprint('money', __name__)

@money_bp.route('/add_money', methods=['GET', 'POST'])
def add_money():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        method = request.form['method']
        source_number = request.form['source_number']
        amount = float(request.form['amount'])
        trx_id = str(uuid.uuid4())[:8]

        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))

        user.balance = (user.balance or 0) + amount

        trx = Transaction(
            user_id=user.id,
            trx_id=trx_id,
            type='add',
            amount=amount,
            method=method,
            source_dest=source_number
        )

        db.session.add(trx)
        db.session.commit()

        flash(f"Successfully added {amount} via {method}.")
        return redirect(url_for('dashboard.dashboard'))

    return render_template('add_money.html')


# Add Money via Bank Account
@money_bp.route('/bank', methods=['GET', 'POST'])
def add_money_bank():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        account_no = request.form.get('accountNo', '').strip()
        amount_raw = request.form.get('amount', '').strip()

        # Basic validation
        if not account_no:
            flash('Bank account number is required.')
            return render_template('bank.html', success=False)

        try:
            amount = float(amount_raw)
        except Exception:
            flash('Amount must be a valid number.')
            return render_template('bank.html', success=False)

        if amount <= 0:
            flash('Amount must be greater than 0.')
            return render_template('bank.html', success=False)

        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))

        # Update balance and create transaction
        user.balance = (user.balance or 0) + amount
        trx_id = str(uuid.uuid4())[:8]
        masked_acc = account_no if len(account_no) < 4 else ("****" + account_no[-4:])
        trx = Transaction(
            user_id=user.id,
            trx_id=trx_id,
            type='add',
            amount=amount,
            method='bank',
            source_dest=masked_acc
        )

        db.session.add(trx)
        db.session.commit()

        # Show success popup on the same page per template logic
        return render_template('bank.html', success=True)

    # GET
    return render_template('bank.html', success=False)


# Add Money via Credit/Debit Card
@money_bp.route('/card', methods=['GET', 'POST'])
def add_money_card():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        card_no = request.form.get('cardNo', '').replace(' ', '').strip()
        amount_raw = request.form.get('amount', '').strip()
        expiry = request.form.get('expiry', '').strip()
        cvc = request.form.get('cvc', '').strip()

        # Basic validation
        if not card_no or len(card_no) < 12:
            flash('Enter a valid card number.')
            return redirect(url_for('money.add_money_card'))

        try:
            amount = float(amount_raw)
        except Exception:
            flash('Amount must be a valid number.')
            return redirect(url_for('money.add_money_card'))

        if amount <= 0:
            flash('Amount must be greater than 0.')
            return redirect(url_for('money.add_money_card'))

        if not expiry or not cvc:
            flash('Expiry and CVC are required.')
            return redirect(url_for('money.add_money_card'))

        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))

        # Update balance and create transaction
        user.balance = (user.balance or 0) + amount
        trx_id = str(uuid.uuid4())[:8]
        masked_card = card_no if len(card_no) < 4 else ("**** **** **** " + card_no[-4:])
        trx = Transaction(
            user_id=user.id,
            trx_id=trx_id,
            type='add',
            amount=amount,
            method='card',
            source_dest=masked_card
        )

        db.session.add(trx)
        db.session.commit()

        flash(f"Successfully added {amount} via card.")
        return redirect(url_for('dashboard.dashboard'))

    # GET
    return render_template('card.html')



# Step 1: Show choice page for send money method
@money_bp.route('/send_money', methods=['GET'])
def send_money_choice():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('send_money_choice.html')  # This template has buttons for local & international


# Step 2: Send money locally (with PIN check and balance check)
@money_bp.route('/send_money/local', methods=['GET', 'POST'])
def send_money_local():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        recipient_phone = request.form['recipient_phone']
        amount = float(request.form['amount'])
        pin = request.form['pin']
        trx_id = str(uuid.uuid4())[:8]

        sender = User.query.get(session['user_id'])
        if not sender:
            session.clear()
            return redirect(url_for('auth.login'))

        if pin != sender.pin:
            flash("Incorrect PIN.")
            return redirect(url_for('money.send_money_local'))

        if (sender.balance or 0) < amount:
            flash("Insufficient balance.")
            return redirect(url_for('money.send_money_local'))

        recipient = User.query.filter_by(phone=recipient_phone).first()
        if not recipient:
            flash("Recipient not found.")
            return redirect(url_for('money.send_money_local'))

        sender.balance -= amount
        recipient.balance = (recipient.balance or 0) + amount

        trx = Transaction(
            user_id=sender.id,
            trx_id=trx_id,
            type='send',
            amount=amount,
            method='wallet',
            source_dest=recipient_phone
        )

        db.session.add(trx)
        db.session.commit()

        flash(f"Sent {amount} to {recipient_phone}.")
        return redirect(url_for('dashboard.dashboard'))

    return render_template('send_money_local.html')


# Step 3: Send money internationally (BDT to USD conversion, PIN check)
@money_bp.route('/send_money/international', methods=['GET'])
def send_money_international():
    # For GET, just render the international send form
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('send_money_international.html')


# New route: handle POST from fetch /submit_transaction (international send JSON)
@money_bp.route('/submit_transaction', methods=['POST'])
def submit_transaction():
    if 'user_id' not in session:
        return jsonify(success=False, message="User not logged in"), 401

    data = request.get_json()
    if not data:
        return jsonify(success=False, message="Invalid JSON data"), 400

    account_no = data.get('account_no')
    receivers_name = data.get('receivers_name')
    country = data.get('country')
    amount_bdt = data.get('amount')

    # Basic validation
    if not all([account_no, receivers_name, country, amount_bdt]):
        return jsonify(success=False, message="Missing required fields"), 400

    try:
        amount_bdt = float(amount_bdt)
        if amount_bdt <= 0:
            return jsonify(success=False, message="Invalid amount"), 400
    except:
        return jsonify(success=False, message="Amount must be a number"), 400

    EXCHANGE_RATE = 130  # BDT to USD conversion rate

    sender = User.query.get(session['user_id'])
    if not sender:
        session.clear()
        return jsonify(success=False, message="Session expired, please log in again"), 401

    if (sender.balance or 0) < amount_bdt:
        return jsonify(success=False, message="Insufficient balance"), 400

    # Deduct balance
    sender.balance -= amount_bdt

    # Convert BDT to USD for transaction record
    amount_usd = round(amount_bdt / EXCHANGE_RATE, 2)

    trx_id = str(uuid.uuid4())[:8]
    trx = Transaction(
        user_id=sender.id,
        trx_id=trx_id,
        type='send_international',
        amount=amount_usd,
        method='international',
        source_dest=f"{account_no} ({receivers_name}, {country})"
    )

    db.session.add(trx)
    db.session.commit()

    return jsonify(success=True)
