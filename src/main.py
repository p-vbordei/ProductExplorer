#####################
# main.py
# %%
from flask import jsonify, request
import os

from src import app, connex_app
from src.investigations import start_investigation
from src.data_acquisition import execute_data_acquisition
from src.products_processing import run_products_investigation
from src.reviews_processing import run_reviews_investigation
from src.run_investigation import run_end_to_end_investigation
from src.users import (create_user, get_user, subscribe_user, log_payment, 
                       subscribe_user_to_package)
from src.firebase_utils import initialize_firestore
# %%

# %%
db = initialize_firestore()

def api_start_investigation():
    """
    Initiates a new investigation based on the provided user ID and list of ASINs.
    """
    data = request.json
    userId = data.get('userId')
    asinList = data.get('asinList')
    
    if not userId or not asinList:
        return jsonify({"error": "userIDs and asinList are required"}), 400

    try:
        result = start_investigation(data, db)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def api_run_data_acquisition():
    """
    Initiates data acquisition based on the provided list of ASINs.
    """
    data = request.json
    asinList = data.get('asinList')
    
    if not asinList:
        return jsonify({"error": "asinList are required"}), 400

    try:
        result = execute_data_acquisition(asinList)
        if result:
            return jsonify({"message": "Data acquisition completed successfully"}), 200
        else:
            return jsonify({"error": "Data acquisition failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def api_run_products_investigation():
    """
    Initiates a product investigation based on the provided investigation ID and credential path.
    """
    data = request.json
    investigationId = data.get('investigationId')
    
    if not investigationId:
        return jsonify({"error": "investigationId is required"}), 400

    try:
        run_products_investigation(investigationId)
        return jsonify({"message": "Investigation completed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def api_run_reviews_investigation():
    """
    Initiates a reviews investigation based on the provided investigation ID and credential path.
    """
    data = request.json
    investigationId = data.get('investigationId')
    
    if not investigationId:
        return jsonify({"error": "investigationId is required"}), 400

    try:
        run_reviews_investigation(investigationId)
        return jsonify({"message": "Reviews investigation completed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def api_run_end_to_end_investigation():
    """
    Initiates an end-to-end investigation based on the provided user ID and list of ASINs.
    """
    data = request.json
    userId = data.get('userId')
    asinList = data.get('asinList')
    
    if not userId or not asinList:
        return jsonify({"error": "userId and asinList are required"}), 400

    try:
        result = run_end_to_end_investigation(data)
        if result:
            return jsonify({"message": "End-to-end investigation completed successfully"}), 200
        else:
            return jsonify({"error": "End-to-end investigation failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def api_create_user(db = db):
    data = request.json
    try:
        userId = create_user(data, db)
        return jsonify({"userId": userId}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def api_get_user(db = db):
    userId = request.args.get('userId')
    if not userId:
        return jsonify({"error": "userId is required"}), 400
    user_data = get_user(userId, db)
    if user_data:
        return jsonify(user_data), 200
    else:
        return jsonify({"error": "User not found"}), 404


def api_subscribe_user(db = db):
    data = request.json
    userId = data.get('userId')
    package = data.get('package')
    if not userId or not package:
        return jsonify({"error": "userId and package are required"}), 400
    try:
        subscription_data = subscribe_user(userId, package, db)
        return jsonify(subscription_data), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def api_log_payment(db = db):
    data = request.json
    try:
        payment_id = log_payment(data, db)
        return jsonify({"paymentId": payment_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def api_subscribe_user_to_package(db = db):
    data = request.json
    userId = data.get('userId')
    package = data.get('package')
    start_date = data.get('startDate')
    payment_intent_id = data.get('paymentIntentId')
    if not all([userId, package, start_date, payment_intent_id]):
        return jsonify({"error": "All fields are required"}), 400
    try:
        subscribe_user_to_package(userId, package, start_date, payment_intent_id, db)
        return jsonify({"message": "Subscription successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=8080)
# ====================================