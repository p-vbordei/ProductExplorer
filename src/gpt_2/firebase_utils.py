# Description: Utility functions for interacting with Firestore
# firebase_utils.py

from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials, firestore
import os

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




############################################ SAVE RESULTS TO FIRESTORE ############################################

def save_results_to_firestore(df_with_clusters, clean_reviews_list):
    """Save processed reviews and their clusters to Firestore."""
    
    print('df_with_clusters')
    print(df_with_clusters.columns)
    print("--------------------")
    
    merge_reviews_df = pd.DataFrame(clean_reviews_list)

    print('merge_reviews_df')
    print(merge_reviews_df.columns)
    print("--------------------")
    print("Columns in df_with_clusters:", df_with_clusters.columns)
    print("Columns in merge_reviews_df:", merge_reviews_df.columns)
    print("Duplicate IDs in df_with_clusters:", df_with_clusters['id'].duplicated().sum())
    print("Duplicate IDs in merge_reviews_df:", merge_reviews_df['id'].duplicated().sum())

    merge_columns_proposed = ['review', 'name', 'date', 'asin', 'id', 'review_data', 'rating','title', 'media', 'verified_purchase', 'num_tokens','review_num_tokens',]
    merge_columns = list(set(merge_columns_proposed).intersection(set(merge_reviews_df.columns)))

    print('merge columns')
    print(merge_columns)

    reviews_with_clusters = df_with_clusters.merge(merge_reviews_df[merge_columns], on = ['id'], how = 'left')

    print("------------ reviews with clusters columns----------------------------")       
    print(reviews_with_clusters.columns)
    save_reviews_with_clusters_to_firestore(reviews_with_clusters)
