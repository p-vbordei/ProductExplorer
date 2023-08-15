from flask import Flask, request, jsonify, abort
import firebase_admin
from firebase_admin import credentials, firestore
import stripe
import os
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Firebase Admin SDK
cred = credentials.Certificate(os.environ.get('FIREBASE_SERVICE_ACCOUNT'))
firebase_admin.initialize_app(cred)
db = firestore.client()

# Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Modules
from users import create_user as create_user_db, get_user as get_user_db, subscribe_user as subscribe_user_db, log_payment
from investigations import start_investigation as start_investigation_db, get_investigation as get_investigation_db, complete_investigation
from modeling import generate_model_results
from reporting import generate_report as generate_report_db

@app.route('/webhook', methods=['POST'])
def webhook():
    # TODO: Handle Stripe webhooks
    return jsonify({'status': 'Webhook received'}), 200

@app.route('/users', methods=['POST'])
def create_user_route():
    try:
        user = request.get_json()
        user_id = create_user_db(user, db)
        return jsonify({'user_id': user_id}), 201
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        abort(500)

@app.route('/users/<user_id>') 
def get_user_route(user_id):
    try:
        user = get_user_db(user_id, db)
        return jsonify(user), 200
    except Exception as e:
        logging.error(f"Error fetching user {user_id}: {e}")
        abort(500)

@app.route('/users/<user_id>/subscribe', methods=['POST'])
def subscribe(user_id):
    try:
        data = request.get_json()
        subscription = subscribe_user_db(user_id, data['package'], db)  
        return jsonify(subscription), 200
    except Exception as e:
        logging.error(f"Error subscribing user {user_id}: {e}")
        abort(500)

@app.route('/investigations', methods=['POST'])
def start_investigation_route():
    try:
        data = request.get_json()
        investigation = start_investigation_db(data, db)
        return jsonify(investigation), 201
    except Exception as e:
        logging.error(f"Error starting investigation: {e}")
        abort(500)

@app.route('/investigations/<investigation_id>')
def get_investigation_route(investigation_id):
    try:
        investigation = get_investigation_db(investigation_id, db)
        return jsonify(investigation), 200
    except Exception as e:
        logging.error(f"Error fetching investigation {investigation_id}: {e}")
        abort(500)

@app.route('/modeling/<investigation_id>')  
def generate_modeling(investigation_id):
    try:
        results = generate_model_results(investigation_id, db)
        return jsonify(results), 200
    except Exception as e:
        logging.error(f"Error generating model results for investigation {investigation_id}: {e}")
        abort(500)

@app.route('/reports/<investigation_id>')
def generate_report_route(investigation_id):
    try:
        report = generate_report_db(investigation_id, db) 
        return jsonify(report), 200
    except Exception as e:
        logging.error(f"Error generating report for investigation {investigation_id}: {e}")
        abort(500)

if __name__ == '__main__':
    app.run(debug=True)
