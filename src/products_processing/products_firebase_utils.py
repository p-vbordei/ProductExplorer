# Description: Utility functions for interacting with Firestore
# products_firebase_utils.py

from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import logging
import requests

# Firestore details
CRED_PATH = '/Users/vladbordei/Documents/Development/ProductExplorer/notebooks/productexplorerdata-firebase-adminsdk-ulb3d-465f23dff3.json'


"""# Initialize Firestore
cred = credentials.Certificate(cred_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()
"""


def initialize_firestore(CRED_PATH):
    """Initialize Firestore client."""
    cred = credentials.Certificate(CRED_PATH)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    return db


def get_asins_from_investigation(investigation_id, db):
    # Retrieve the investigation from Firestore
    investigation_ref = db.collection(u'investigations').document(investigation_id)
    investigation = investigation_ref.get()

    if investigation.exists:
        # Retrieve the asins from the investigation
        asins = investigation.get('asins')
        return asins
    else:
        print('Investigation does not exist')
        return None

def get_product_details_from_asin(asin, db):
    # Retrieve the product details from Firestore
    product_ref = db.collection('products').document(asin)
    product = product_ref.get()

    if product.exists:
        product_details = product.get('details')
        return product_details
    else:
        print(f'No product details found for ASIN {asin}')
        return None

def get_investigation_and_product_details(investigation_id, db):
    asins = get_asins_from_investigation(investigation_id, db)
    products = []

    if asins is not None:
        for asin in asins:
            product_details = get_product_details_from_asin(asin, db)
            if product_details is not None:
                products.append(product_details)
    return products

def update_investigation_status(investigation_id, new_status,db):
    investigation_ref = db.collection(u'investigations').document(investigation_id)
    investigation = investigation_ref.get()
    if investigation.exists:
        investigation_ref.update({
            'status': new_status,
            f'{new_status}_timestamp': firestore.SERVER_TIMESTAMP,
        })
        return True  # update was successful
    else:
        return False  # investigation does not exist
    

def update_firestore_individual_products(new_products_list, INVESTIGATION, db):
    # Update the Firestore database
    for product in tqdm(new_products_list):
        doc_ref = db.collection('products').document(product['asin'])
        try:
            doc_ref.set(asin_level_data, merge=True)  # Use set() with merge=True to update or create a new document
        except Exception as e:
            print(f"Error updating document {product['asin']}: {e}")


def save_product_details_to_firestore(db, investigation_id, product_data):
    """
    Save or update product data to Firestore.

    Parameters:
    - db (object): Firestore database client.
    - investigation_id (str): The ID of the investigation.
    - product_data (dict): The product data to save or update.

    Returns:
    - bool: True if successful, False otherwise.
    """
    
    doc_ref = db.collection('insights').document(investigation_id)
    try:
        doc_ref.set(product_data, merge=True)  # Use set() with merge=True to update or create a new document
        logging.info(f"Successfully saved/updated investigation results with id {investigation_id}")
        return True
    except Exception as e:
        logging.error(f"Error saving/updating investigation results with id {investigation_id}: {e}", exc_info=True)
        return False

