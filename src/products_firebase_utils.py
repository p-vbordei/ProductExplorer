# Description: Utility functions for interacting with Firestore
# products_firebase_utils.py

from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials, firestore
import logging
from tqdm import tqdm


def initialize_firestore():
    """Initialize Firestore client."""

    # Firestore details
    CRED_PATH = '/Users/vladbordei/Documents/Development/ProductExplorer/notebooks/productexplorerdata-firebase-adminsdk-ulb3d-465f23dff3.json'

    cred = credentials.Certificate(CRED_PATH)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    return db


def get_asins_from_investigation(investigationId, db):
    # Retrieve the investigation from Firestore
    investigation_ref = db.collection(u'investigations').document(investigationId)
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
        productDetails = product.get('details')
        return productDetails
    else:
        print(f'No product details found for ASIN {asin}')
        return None

def get_investigation_and_product_details(investigationId, db):
    asins = get_asins_from_investigation(investigationId, db)
    products = []

    if asins is not None:
        for asin in asins:
            productDetails = get_product_details_from_asin(asin, db)
            if productDetails is not None:
                products.append(productDetails)
    return products

def update_investigation_status(investigationId, newStatus,db):
    investigation_ref = db.collection(u'investigations').document(investigationId)
    investigation = investigation_ref.get()
    if investigation.exists:
        investigation_ref.update({
            'status': newStatus,
            f'{newStatus}_timestamp': firestore.SERVER_TIMESTAMP,
        })
        return True  # update was successful
    else:
        return False  # investigation does not exist
    

def update_firestore_individual_products(newProductsList, investigationId, db):
    # Update the Firestore database
    for product in tqdm(newProductsList):
        doc_ref = db.collection('products').document(product['asin'])
        try:
            doc_ref.set(product, merge=True)  # Use set() with merge=True to update or create a new document
        except Exception as e:
            print(f"Error updating document {product['asin']}: {e}")


def save_product_details_to_firestore(db, investigationId, productData):
    """
    Save or update product data to Firestore.

    Parameters:
    - db (object): Firestore database client.
    - investigationId (str): The ID of the investigation.
    - productData (dict): The product data to save or update.

    Returns:
    - bool: True if successful, False otherwise.
    """
    
    doc_ref = db.collection('insights').document(investigationId)
    try:
        doc_ref.set(productData, merge=True)  # Use set() with merge=True to update or create a new document
        logging.info(f"Successfully saved/updated investigation results with id {investigationId}")
        return True
    except Exception as e:
        logging.error(f"Error saving/updating investigation results with id {investigationId}: {e}", exc_info=True)
        return False

