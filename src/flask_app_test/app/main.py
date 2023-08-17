#####################
# main.py
from flask import jsonify, request
import os
import sys
sys.path.append('.')
from . import app, connex_app

from .products_processing import run_products_investigation


@app.route('/run_products_investigation', methods=['POST'])
def api_run_products_investigation():
    """
    Initiates a product investigation based on the provided investigation ID and credential path.
    """
    data = request.json
    investigation_id = data.get('investigation_id')
    cred_path = data.get('cred_path')
    
    if not investigation_id or not cred_path:
        return jsonify({"error": "investigation_id and cred_path are required"}), 400

    try:
        run_products_investigation(investigation_id, cred_path)
        return jsonify({"message": "Investigation completed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    load_dotenv()
    INVESTIGATION = "investigationId2"
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    connex_app.run(port=8080)
#####################