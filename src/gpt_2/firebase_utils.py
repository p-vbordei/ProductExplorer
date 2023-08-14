# Description: Utility functions for interacting with Firestore
# firebase_utils.py

from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials, firestore
import os
import pandas as pd
import time
from collections import defaultdict


# Firestore details
cred_path = '/Users/vladbordei/Documents/Development/ProductExplorer/notebooks/productexplorerdata-firebase-adminsdk-ulb3d-465f23dff3.json'

# Initialize Firestore
cred = credentials.Certificate(cred_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()


def update_investigation_status(investigation_id, new_status):
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
    

def get_asins_from_investigation(investigation_id):
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


def get_reviews_from_asin(asin):
    # Retrieve the reviews from Firestore
    reviews_query = db.collection('products').document(asin).collection('reviews').stream()

    # Store all reviews in a list
    product_reviews = []
    for review in reviews_query:
        product_reviews.append(review.to_dict())

    if product_reviews:
        return product_reviews
    else:
        print(f'No product reviews found for ASIN {asin}')
        return None

def get_investigation_and_reviews(investigation_id):
    asins = get_asins_from_investigation(investigation_id)
    reviews_list = []

    if asins is not None:
        for asin in asins:
            asin_reviews = get_reviews_from_asin(asin)
            if asin_reviews is not None:
                reviews_list.append(asin_reviews)
    return reviews_list


def write_reviews(clean_reviews_list):
    # Group reviews by ASIN
    reviews_by_asin = defaultdict(list)
    for review in clean_reviews_list:
        asin_string = review['asin']['original'] if isinstance(review['asin'], dict) else review['asin']
        reviews_by_asin[asin_string].append(review)

    start_time = time.time()

    # Write reviews for each ASIN in a batch
    for asin_string, reviews in reviews_by_asin.items():
        batch = db.batch()

        for review in reviews:
            review_id = review['id']

            review_ref = db.collection('products').document(asin_string).collection('reviews').document(review_id)
            batch.set(review_ref, review, merge=True)
        try:
            batch.commit()
            print(f"Successfully saved/updated reviews for ASIN {asin_string}")
        except Exception as e:
            print(f"Error saving/updating reviews for ASIN {asin_string}: {e}")

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"Successfully saved/updated all reviews. Time taken: {elapsed_time} seconds")


def update_to_firestore_reviews_with_cluster_info(reviews_with_clusters):
    """
    Save the reviews with clusters to Firestore.
    
    Parameters:
    - reviews_with_clusters (DataFrame): DataFrame containing reviews with cluster information.
    """
    # Group reviews by ASIN
    grouped_reviews = reviews_with_clusters.groupby('asin_original')
    data_for_upload = {asin_original: group.drop(columns='asin_original').to_dict(orient='records') for asin_original, group in grouped_reviews}

    start_time = time.time()

    # Write reviews for each ASIN in a batch
    for asin_original, reviews in data_for_upload.items():
        if len(reviews) > 500:
            print(f"Warning: More than 500 reviews for ASIN {asin_original}. Consider splitting the reviews or handling them differently.")
            continue

        batch = db.batch()
        for review in reviews:
            review_id = review['id']
            review_ref = db.collection('products').document(asin_original).collection('reviews').document(review_id)
            batch.set(review_ref, review, merge=True)
        try:
            batch.commit()
            print(f"Successfully saved/updated reviews for ASIN {asin_original}")
        except Exception as e:
            print(f"Error saving/updating reviews for ASIN {asin_original}: {e}")

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"Successfully saved/updated all reviews with clusters. Time taken: {elapsed_time} seconds")