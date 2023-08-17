#####################
# main.py
from flask import Flask, jsonify, request
import connexion
import os
from app.products_processing import run_products_investigation

# Create a Flask app instance
app = Flask(__name__)

# Create a Connexion app instance
connex_app = connexion.App(__name__, specification_dir='./')
connex_app.add_api('swagger.yaml')

@app.route('/run_products_investigation', methods=['POST'])
def api_run_products_investigation():
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
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    connex_app.run(port=8080)
#####################