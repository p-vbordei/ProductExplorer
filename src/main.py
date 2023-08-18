#####################
# main.py
from flask import jsonify, request
import os
from dotenv import load_dotenv

from src import app, connex_app
from src.products_processing import run_products_investigation
from src.reviews_processing import run_reviews_investigation
from src.investigations import start_investigation


def api_start_investigation():
    """
    Initiates a new investigation based on the provided user ID and list of ASINs.
    """
    data = request.json
    user_id = data.get('user_id')
    asins = data.get('asins')
    
    if not user_id or not asins:
        return jsonify({"error": "user_id and asins are required"}), 400

    try:
        result = start_investigation(data, db)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def api_run_products_investigation():
    """
    Initiates a product investigation based on the provided investigation ID and credential path.
    """
    data = request.json
    investigation_id = data.get('investigation_id')
    
    if not investigation_id:
        return jsonify({"error": "investigation_id is required"}), 400

    try:
        run_products_investigation(investigation_id)
        return jsonify({"message": "Investigation completed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def api_run_reviews_investigation():
    """
    Initiates a reviews investigation based on the provided investigation ID and credential path.
    """
    data = request.json
    investigation_id = data.get('investigation_id')
    
    if not investigation_id:
        return jsonify({"error": "investigation_id is required"}), 400

    try:
        run_reviews_investigation(investigation_id)
        return jsonify({"message": "Reviews investigation completed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    load_dotenv()
    INVESTIGATION = "investigationId2"
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    connex_app.run(port=8080)
# ====================================