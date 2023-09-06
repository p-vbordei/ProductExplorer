#######################
# Description: Utility functions for interacting with Firestore
# firebase_utils.py

import os
import json
from collections import defaultdict
import logging

from google.cloud import firestore, secretmanager
import firebase_admin
from firebase_admin import credentials, firestore

from tqdm import tqdm
import time


try:
    from src.investigations import get_asins_from_investigation, update_investigation_status
except ImportError:
    from investigations import get_asins_from_investigation, update_investigation_status


def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    project_id = "productexplorerdata"
    secret_version_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": secret_version_name})
    return response.payload.data.decode('UTF-8')

def initialize_firestore():
    """Initialize Firestore client."""

    # Check if running on App Engine
    if os.environ.get('GAE_ENV', '').startswith('standard'):
        # Running on App Engine, use default credentials
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
    else:
        # Try to get the key content from environment variable
        FIREBASE_KEY = os.getenv("FIREBASE_KEY")

        # If not found, try to get from secret management
        if not FIREBASE_KEY:
            try:
                FIREBASE_KEY = get_secret("FIREBASE_KEY")
            except Exception as e:
                logging.error(f"Error fetching FIREBASE_KEY from secret manager: {e}")

        # If still not found, load from .env (for local development)
        if not FIREBASE_KEY:
            from dotenv import load_dotenv
            load_dotenv()
            FIREBASE_KEY = os.getenv("FIREBASE_KEY")

        if not FIREBASE_KEY:
            raise ValueError("FIREBASE_KEY not found in environment or secrets")

        # Check if FIREBASE_KEY is a path to a file
        if os.path.exists(FIREBASE_KEY):
            with open(FIREBASE_KEY, 'r') as file:
                cred_data = json.load(file)
        else:
            # Try to parse the key content as JSON
            try:
                cred_data = json.loads(FIREBASE_KEY)
            except json.JSONDecodeError:
                logging.error("Failed to parse FIREBASE_KEY content")
                raise ValueError("Failed to parse FIREBASE_KEY as JSON")

        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_data)
            firebase_admin.initialize_app(cred)

    db = firestore.client()
    return db




########### PRODUCTS #############


def get_product_details_from_asin(asin, db):
    try:
        # Retrieve the product details from Firestore
        product_ref = db.collection('products').document(asin)
        product = product_ref.get()
    except Exception as e:
        logging.error(f"Error retrieving product details for ASIN {asin}: {e}")
        return None

    if product.exists:
        try:
            productDetails = product.get('details')
            return productDetails
        except Exception as e:
            logging.error(f"Error getting 'details' field for ASIN {asin}: {e}")
            return None
    else:
        logging.warning(f'No product details found for ASIN {asin}')
        return None

def get_investigation_and_product_details(investigationId, db):
    try:
        asinList = get_asins_from_investigation(investigationId, db)
    except Exception as e:
        logging.error(f"Error getting ASINs for investigation {investigationId}: {e}")
        return []

    products = []

    if asinList is not None:
        for asin in asinList:
            try:
                productDetails = get_product_details_from_asin(asin, db)
                if productDetails is not None:
                    productDetails['asin'] = asin
                    products.append(productDetails)
            except Exception as e:
                logging.error(f"Error appending product details for ASIN {asin}: {e}")
                continue

    return products

def update_firestore_individual_products(newProductsList, db):
    # Update the Firestore database
    for product in tqdm(newProductsList):
        doc_ref = db.collection('products').document(product['asin'])
        try:
            doc_ref.set(product, merge=True)  # Use set() with merge=True to update or create a new document
        except Exception as e:
            logging.error(f"Error updating document {product['asin']}: {e}")

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
    
    doc_ref = db.collection('productInsights').document(investigationId)
    try:
        doc_ref.set(productData, merge=True)  # Use set() with merge=True to update or create a new document
        logging.info(f"Successfully saved/updated investigation results with id {investigationId}")
        return True
    except Exception as e:
        logging.error(f"Error saving/updating investigation results with id {investigationId}: {e}", exc_info=True)
        return False

def get_product_data_from_investigation(db, investigationId):
    """
    Retrieve product data from Firestore based on an investigation ID.

    Parameters:
    - db (object): Firestore database client.
    - investigationId (str): The ID of the investigation.

    Returns:
    - dict: The product data retrieved.
    - None: If there's an error or the investigation doesn't exist.
    """

    # Retrieve the product data from Firestore using the investigation ID
    productDataRef = db.collection('productInsights').document(investigationId)
    productData = productDataRef.get()

    # Check if the document exists
    if productData.exists:
        return productData.to_dict()
    else:
        logging.warning(f"Investigation with id {investigationId} does not exist in 'productInsights'")
        return None


########### REVIEWS #############

def get_reviews_from_asin(asin, db):
    try:
        # Retrieve the reviews from Firestore
        reviews_query = db.collection('products').document(asin).collection('reviews').stream()
    except Exception as e:
        logging.error(f"Error retrieving reviews for ASIN {asin}: {e}")
        return None

    # Store all reviews in a list
    productReviews = []
    for review in reviews_query:
        try:
            review_data = review.to_dict()
            review_data['asin'] = asin  # Add the 'asin' key to each review
            productReviews.append(review_data)
        except Exception as e:
            logging.error(f"Error processing review for ASIN {asin}: {e}")
            continue

    if productReviews:
        return productReviews
    else:
        logging.warning(f'No product reviews found for ASIN {asin}')
        return None

def get_investigation_and_reviews(investigationId, db):
    try:
        asinList = get_asins_from_investigation(investigationId, db)
    except Exception as e:
        logging.error(f"Error getting ASINs for investigation {investigationId}: {e}")
        return []

    reviewsList = []

    if asinList is not None:
        for asin in asinList:
            try:
                asinReviews = get_reviews_from_asin(asin, db)
                if asinReviews is not None:
                    reviewsList.append(asinReviews)
            except Exception as e:
                logging.error(f"Error appending reviews for ASIN {asin}: {e}")
                continue

    return reviewsList

def get_clean_reviews(investigationId, db):
    """Retrieve and clean reviews."""
    try:
        update_investigation_status(investigationId, "startedReviews", db)
    except Exception as e:
        logging.error(f"Error updating investigation status for {investigationId}: {e}")

    try:
        reviews_download = get_investigation_and_reviews(investigationId, db)
        flattened_reviews = [item for sublist in reviews_download for item in sublist]
    except Exception as e:
        logging.error(f"Error flattening reviews for investigation {investigationId}: {e}")
        return []

    return flattened_reviews

def write_reviews_to_firestore(cleanReviewsList, db):
    # Group reviews by ASIN
    reviewsByAsin = defaultdict(list)
    for review in cleanReviewsList:
        asinString = review['asin']
        reviewsByAsin[asinString].append(review)

    startTime = time.time()

    # Write reviews for each ASIN in a batch
    for asinString, reviews in reviewsByAsin.items():
        batch = db.batch()

        for review in reviews:
            review_id = review['id']
            review_ref = db.collection('products').document(asinString).collection('reviews').document(review_id)
            try:
                batch.set(review_ref, review, merge=True)
            except Exception as e:
                logging.error(f"Error adding review to batch for ASIN {asinString}: {e}")
                continue

        try:
            batch.commit()
            logging.info(f"Successfully saved/updated reviews for ASIN {asinString}")
        except Exception as e:
            logging.error(f"Error saving/updating reviews for ASIN {asinString}: {e}")

    endTime = time.time()
    elapsedTime = endTime - startTime

    logging.info(f"Successfully saved/updated all reviews. Time taken: {elapsedTime} seconds")


def save_cluster_info_to_firestore(attributeClustersWithPercentage, attributeClustersWithPercentageByAsin, investigationId, db):
    """
    Save the clusters to Firestore.
    
    Parameters:
    - attributeClustersWithPercentage (DataFrame): DataFrame containing attribute clusters with percentage information.
    - attributeClustersWithPercentageByAsin (DataFrame): DataFrame containing attribute clusters with percentage information by ASIN.
    - investigationId (str): The ID of the investigation.
    """
    try:
        # Create a dictionary with the cluster information
        clusters_dict = {
            'attributeClustersWithPercentage': attributeClustersWithPercentage.to_dict(orient='records'),
            'attributeClustersWithPercentageByAsin': attributeClustersWithPercentageByAsin.to_dict(orient='records'),
        }

        startTime = time.time()

        cluster_ref = db.collection(u'clusters').document(investigationId)
        cluster = cluster_ref.get()
        if cluster.exists:
            cluster_ref.update(clusters_dict)
        else:
            cluster_ref.set(clusters_dict)

        endTime = time.time()
        elapsedTime = endTime - startTime

        logging.info(f"Successfully saved/updated clusters to firestore. Time taken: {elapsedTime} seconds")
    except Exception as e:
        logging.error(f"Error saving/updating clusters to firestore for investigation {investigationId}: {e}")

def write_insights_to_firestore(investigationId, datapointsDict, db):
    try:
        batch = db.batch()

        startTime = time.time()
        for attribute, datapoints_list in datapointsDict.items():
            # Ensure all numbers are either int or float
            for datapoint in datapoints_list:
                datapoint['observationCount'] = int(datapoint['observationCount'])
                datapoint['totalNumberOfObservations'] = int(datapoint['totalNumberOfObservations'])
                datapoint['percentageOfObservationsVsTotalNumberPerAttribute'] = float(datapoint['percentageOfObservationsVsTotalNumberPerAttribute'])
                datapoint['percentageOfObservationsVsTotalNumberOfReviews'] = float(datapoint['percentageOfObservationsVsTotalNumberOfReviews'])

            doc_ref = db.collection(u'reviewsInsights').document(investigationId).collection(u'attributeWithPercentage').document(attribute)
            batch.set(doc_ref, {
                u'clusters': datapoints_list
            })

        batch.commit()
        endTime = time.time()
        elapsedTime = endTime - startTime
        logging.info(f"Data for {investigationId} successfully written to Firestore. Time taken: {elapsedTime} seconds")
    except Exception as e:
        logging.error(f"Error writing data for {investigationId} to Firestore: {e}")


# ===================