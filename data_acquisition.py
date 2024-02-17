###################### DATA ACQUISITION ######################
# data_acquisition.py
# https://rapidapi.com/eaidoo015-pj8dZiAnLJJ/api/youtube-scraper-2023/pricing
# https://rapidapi.com/felixeschmittfes/api/amazonlive/pricing
# %%

import requests
import time
import asyncio
import nest_asyncio
import aiohttp
from google.cloud import firestore, secretmanager
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

# Amazon Scraper details
product_url = "https://amazonlive.p.rapidapi.com/product"
reviews_url = "https://amazonlive.p.rapidapi.com/reviews"
headers = {
    "X-RapidAPI-Key": "4da31a08e5mshaca05d98a3d9d6ep1fffb1jsn019717508cc8",
    "X-RapidAPI-Host": "amazonlive.p.rapidapi.com"
}

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


def get_product_details(asin, retries=3):
    start = time.time()
    params = {"asin": asin, "location": "us"}
    for _ in range(retries):
        response = requests.get(product_url, headers=headers, params=params)
        if response.status_code == 429:  # Rate limit hit
            time.sleep(2)  # Wait for 2 seconds
            continue
        elif response.status_code != 200:
            print(f"Failed to fetch product details for {asin}. HTTP status: {response.status_code}")
            return None
        print(f"Fetching product details for {asin} took {time.time() - start} seconds.")
        return response.json()
    print(f"Failed to fetch product details for {asin} after {retries} retries.")
    return None

def get_product_reviews(asin):
    start = time.time()
    pages = ["1", "2", "3", "4", "5"]
    results = []
    for page_var in pages:
        result = fetch_reviews(page_var, asin)
        if result:
            results.append(result)
    print(f"Fetching product reviews for {asin} took {time.time() - start} seconds.")
    return results

def fetch_reviews(page_var, asin, retries=3):
    params = {
        "asin": asin,
        "location": "us",
        "page": page_var,
        "amount": "20",
        "sort_by_recent": "false",
        "only_verified": "true"
    }
    for _ in range(retries):
        response = requests.get(reviews_url, headers=headers, params=params)
        if response.status_code == 429:  # Rate limit hit
            time.sleep(2)  # Wait for 2 seconds
            continue
        elif response.status_code != 200:
            print(f"Failed to fetch reviews for {asin} page {page_var}. HTTP status: {response.status_code}")
            return None
        return response.json()
    print(f"Failed to fetch reviews for {asin} page {page_var} after {retries} retries.")
    return None

def update_firestore(asin, details, reviews, db):
    if details is None or reviews is None or any(review is None for review in reviews):
        print(f"Skipping Firestore update for {asin} due to missing data.")
        return
    start = time.time()
    doc_ref = db.collection('products').document(asin)
    
    # Set details field in the document
    doc_ref.set({
        'details': details
    }, merge=True)

    # Initialize Firestore batch
    batch = db.batch()
    for review_page in reviews:
        if review_page is not None:
            for review in review_page:  # Directly iterate over review_page
                review_id = review['id']
                review['asin'] = asin
                review_ref = doc_ref.collection('reviews').document(review_id)
                batch.set(review_ref, review)

    # Commit the batch
    batch.commit()

    print(f"Updating Firestore for {asin} took {time.time() - start} seconds.")

def process_asin(asin, db):
    reviews = get_product_reviews(asin)
    if reviews is None or any(review is None for review in reviews):
        print(f"Skipping {asin} due to failed reviews fetch.")
        return
    update_firestore(asin, None, reviews, db)  # Assuming details fetching is handled elsewhere or removed


def run_data_acquisition(asinList):
    try:
        db = initialize_firestore()
        for asin in asinList:
            process_asin(asin, db)
        return True
    except Exception as e:
        print(f"Error during data acquisition: {e}")
        return False
# %%
# ######## TESTING FUNCTIONS #########


# Test function to get product details for the first ASIN
# Assuming asinList is defined somewhere in your script
asinList = ['SampleAsin1', 'SampleAsin2']  # Example ASINs

# Test function to get product details for the first ASIN
def test_get_product_details_for_first_asin():
    asin = asinList[0]
    details = get_product_details(asin)  # Synchronously get product details
    print(f"Product details for ASIN {asin}:")
    print(details)
    return details

# Test function to get reviews for the first ASIN
def test_get_product_reviews_for_first_asin():
    asin = asinList[0]
    reviews = get_product_reviews(asin)  # Synchronously get product reviews
    print(f"Reviews for ASIN {asin}:")
    for review_page in reviews:
        if review_page:
            for review in review_page:  # Directly iterate over review_page
                print(review)
    return reviews

# Test function to write product details and reviews for the first ASIN to Firebase
def test_write_to_firestore_for_first_asin():
    asin = asinList[0]
    db = initialize_firestore()
    
    # Fetch product details and reviews synchronously
    details = get_product_details(asin)  # If you decide to fetch details synchronously
    reviews = get_product_reviews(asin)
    
    # Write to Firestore
    update_firestore(asin, details, reviews, db)

# %%
###### TESTS #########

# %%

# Product Details
#print("\nFetching product details for the first ASIN...")
#test_get_product_details_for_first_asin()

# %%
# Reviews
#print("\nFetching reviews for the first ASIN...")
#test_get_product_reviews_for_first_asin()
# %%
# Firestore
#print("\nWriting product details and reviews for the first ASIN to Firebase...")
#test_write_to_firestore_for_first_asin()


# %%
# ====================