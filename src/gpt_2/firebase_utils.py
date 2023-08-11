# Description: Utility functions for interacting with Firestore
# firebase_utils.py

from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials, firestore
import os

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
        asin = review['asin']['original']
        reviews_by_asin[asin].append(review)

    start_time = time.time()

    # Write reviews for each ASIN in a batch
    for asin, reviews in reviews_by_asin.items():
        batch = db.batch()

        for review in reviews:
            review_id = review['id']
            review_ref = db.collection('products').document(asin).collection('reviews').document(review_id)
            batch.set(review_ref, review, merge=True)

        try:
            batch.commit()
            print(f"Successfully saved/updated reviews for ASIN {asin}")
        except Exception as e:
            print(f"Error saving/updating reviews for ASIN {asin}: {e}")

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"Successfully saved/updated all reviews. Time taken: {elapsed_time} seconds")


def save_clusters_to_firestore(investigation_id, attribute_clusters, attribute_clusters_by_asin):
    # Get the reference to the investigation document
    investigation_ref = db.collection('Investigations').document(investigation_id)
    
    # Save attribute_clusters to Firestore
    clusters_ref = investigation_ref.collection('clusters').document('attribute_clusters')
    clusters_ref.set({
        'data': attribute_clusters.to_dict(orient='records')  # Convert DataFrame to list of dicts
    })
    
    # Save attribute_clusters_by_asin to Firestore
    clusters_by_asin_ref = investigation_ref.collection('clusters').document('attribute_clusters_by_asin')
    clusters_by_asin_ref.set({
        'data': attribute_clusters_by_asin.to_dict(orient='records')  # Convert DataFrame to list of dicts
    })

def save_reviews_with_clusters_to_firestore(reviews_with_clusters):
    # Iterate over each review in reviews_with_clusters
    for _, review in reviews_with_clusters.iterrows():
        # Get the reference to the product's review document
        review_ref = db.collection('products').document(review['asin']).collection('reviews').document(review['id'])
        
        # Update the review document with cluster information
        review_ref.set({
            'cluster_info': review['cluster_info']  # Assuming 'cluster_info' is the column name in reviews_with_clusters DataFrame
        }, merge=True)  # merge=True ensures that only the 'cluster_info' field is updated, and other fields remain unchanged
