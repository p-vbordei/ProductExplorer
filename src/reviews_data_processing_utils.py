##########################
# data_processing_utils.py

import re
from tiktoken import get_encoding
import logging
logging.basicConfig(level=logging.INFO)
import numpy as np
import pandas as pd
import tiktoken

def num_tokens_from_string(string: str, encoding_name="cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    try:
        encoding = get_encoding(encoding_name)
        return len(encoding.encode(string))
    except Exception as e:
        logging.error(f"Error counting tokens: {e}")
        return 0

def clean_review(review_body):
    try:
        return re.sub(r'[^a-zA-Z0-9\s]+', '', review_body)
    except TypeError as e:
        logging.error(f"Error cleaning review: {e}")
        return ""

def initial_review_clean_data(df, limit=3000):
    try:
        df.loc[:, 'review'] = df['review'].apply(clean_review)
        df.loc[:, 'num_tokens'] = df['review'].apply(num_tokens_from_string)
        df.loc[:, 'review'] = df.apply(lambda x: x['review'][:limit * 3] if x['num_tokens'] > limit else x['review'], axis=1)
        df.loc[:, 'review_num_tokens'] = df['review'].apply(num_tokens_from_string)
        return df
    except Exception as e:
        logging.error(f"Error in initial_review_clean_data: {e}")
        return df

def initial_review_clean_data_list(reviews_list, limit=3000):
    try:
        for review_dict in reviews_list:
            review_dict['review'] = clean_review(review_dict['review'])
            review_dict['num_tokens'] = num_tokens_from_string(review_dict['review'])
            if review_dict['num_tokens'] > limit:
                review_dict['review'] = review_dict['review'][:limit * 3]
            review_dict['review_num_tokens'] = num_tokens_from_string(review_dict['review'])
        return reviews_list
    except Exception as e:
        logging.error(f"Error in initial_review_clean_data_list: {e}")
        return reviews_list

def process_datapoints(df):
    datapoints_list = []
    try:
        total = round(df['observationCount'].sum(), 0)

        for index, row in df.iterrows():
            data = {
                "attribute": row["attribute"],
                "clusterLabel": row["clusterLabel"],
                "observationCount": row['observationCount'],   # Count of Observations of Attribute Value
                "totalNumberOfObservations": total,  # Count of Observations of Attribute
                "percentageOfObservationsVsTotalNumberPerAttribute": round(row['percentageOfObservationsVsTotalNumberPerAttribute'], 2),
                "percentageOfObservationsVsTotalNumberOfReviews": round(row['percentageOfObservationsVsTotalNumberOfReviews'], 2)
            }
            datapoints_list.append(data)
        return datapoints_list
    except Exception as e:
        logging.error(f"Error in process_datapoints: {e}")
        return datapoints_list



############################################ QUANTIFY OBSERVATIONS ############################################


def quantify_observations(reviewsWithClusters, cleanReviews):
    try:
        """Quantify observations at both the investigation and ASIN levels."""
        
        logging.info(f"Columns in reviewsWithClusters: {reviewsWithClusters.columns}")
        logging.info(f"Columns in cleanReviews DataFrame: {pd.DataFrame(cleanReviews).columns}")
        
        # Merge DataFrames
        df_with_clusters = reviewsWithClusters.merge(pd.DataFrame(cleanReviews), on=['id', 'asin'])

        logging.info(f"Columns in merged DataFrame: {df_with_clusters.columns}")
        logging.info(f"Number of NaN values in 'asin' column: {df_with_clusters['asin'].isna().sum()}")
        logging.info(f"Data type of 'asin' column: {df_with_clusters['asin'].dtype}")
        
        agg_result = df_with_clusters.groupby(['attribute', 'clusterLabel']).agg({
            'rating': lambda x: list(x),
            'id': lambda x: list(x),
            'asin': lambda x: list(x),
            }).reset_index()

        count_result = df_with_clusters.groupby(['attribute', 'clusterLabel']).size().reset_index(name='observationCount')
        attributeClustersWithPercentage = pd.merge(agg_result, count_result, on=['attribute', 'clusterLabel'])

        m = [np.mean([int(r) for r in e]) for e in attributeClustersWithPercentage['rating']]
        k = [int(round(e, 0)) for e in m]
        attributeClustersWithPercentage['rating_avg'] = k

        total_observations_per_attribute = df_with_clusters.groupby('attribute').size()
        attributeClustersWithPercentage = attributeClustersWithPercentage.set_index('attribute')
        attributeClustersWithPercentage['percentageOfObservationsVsTotalNumberPerAttribute'] = attributeClustersWithPercentage['observationCount'] / total_observations_per_attribute * 100
        attributeClustersWithPercentage = attributeClustersWithPercentage.reset_index()

        number_of_reviews = reviewsWithClusters['id'].unique().shape[0]
        attributeClustersWithPercentage['percentageOfObservationsVsTotalNumberOfReviews'] = attributeClustersWithPercentage['observationCount'] / number_of_reviews * 100

        # Quantify observations at the ASIN level
        agg_result_asin = df_with_clusters.groupby(['attribute', 'clusterLabel', 'asin']).agg({
            'rating': lambda x: list(x),
            'id': lambda x: list(x),
        }).reset_index()

        count_result_asin = df_with_clusters.groupby(['attribute', 'clusterLabel', 'asin']).size().reset_index(name='observationCount')
        attributeClustersWithPercentageByAsin = pd.merge(agg_result_asin, count_result_asin, on=['attribute', 'clusterLabel', 'asin'])

        m_asin = [np.mean([int(r) for r in e]) for e in attributeClustersWithPercentageByAsin['rating']]
        k_asin = [int(round(e, 0)) for e in m_asin]
        attributeClustersWithPercentageByAsin['rating_avg'] = k_asin

        df_with_clusters['totalObservationsPerAttributeAsin'] = df_with_clusters.groupby(['attribute', 'asin'])['asin'].transform('count')
        attributeClustersWithPercentageByAsin['percentageOfObservationsVsTotalNumberPerAttribute'] = attributeClustersWithPercentageByAsin['observationCount'] / df_with_clusters['totalObservationsPerAttributeAsin'] * 100
        attributeClustersWithPercentageByAsin['percentageOfObservationsVsTotalNumberOfReviews'] = attributeClustersWithPercentageByAsin['observationCount'] / number_of_reviews * 100

        return attributeClustersWithPercentage, attributeClustersWithPercentageByAsin

    except Exception as e:
        logging.error(f"Error in quantify_observations: {e}")
        return None, None  # Return None in case of error



# =====================




def transform_rating_to_star_format(rating):
    """
    Transforms a numerical or textual rating to a star format.

    Args:
    - rating (int or str): A numerical rating value between 1 to 5 or a textual rating.

    Returns:
    - str: A string representation of the rating in the format "5*" or "1*", or the textual rating followed by a "*".
    """
    
    if isinstance(rating, int) and 1 <= rating <= 5:
        return f"{rating}*"
    elif isinstance(rating, str):
        return f"{rating}*"
    else:
        raise ValueError("Rating must be a number between 1 and 5 or a textual value.")


def add_uid_to_reviews(reviewsList):
    """
    Adds a 'uid' to each review in the reviewsList based on its index and 
    returns a dictionary mapping from 'uid' to 'id'.

    Args:
    - reviewsList (list): List of dictionaries with reviews.

    Returns:
    - tuple: A tuple containing:
        - list: Updated list of reviews with 'uid' added.
        - dict: Dictionary mapping from 'uid' to 'id'.
    """

    # Extract 'id' from each dictionary
    ids = [review['id'] for review in reviewsList]

    # Create DataFrame
    id_uid_df = pd.DataFrame(ids, columns=['id'])
    id_uid_df['uid'] = id_uid_df.index

    # Create a mapping of 'id' to 'uid'
    id_to_uid_mapping = id_uid_df.set_index('id')['uid'].to_dict()

    # Initialize dictionary for 'uid' to 'id' mapping
    uid_to_id_mapping = {}

    # Add 'uid' to each dictionary in reviewsList
    for review in reviewsList:
        review['uid'] = id_to_uid_mapping.get(review['id'], None)
        uid_to_id_mapping[review['uid']] = review['id']

    return reviewsList, uid_to_id_mapping



# SPLIT TO BATCHES OF 'x' tokens
def generate_batches(reviews, max_tokens):
    """
    This function takes a list of reviews and groups them into batches based on token count. Each batch 
    has a token count that doesn't exceed the specified max_tokens limit. It returns a list of batches, 
    where each batch is a list of tuples. Each tuple contains a review ID and its corresponding text.
    
    Args:
        reviews (list of dicts): A list of review dictionaries. Each dictionary has keys 'id' and 'text'.
        max_tokens (int): The maximum number of tokens allowed per batch.

    Returns:
        batches (list): A list of lists, where each inner list represents a batch of tuples.
    """
    batches = []
    current_batch = []
    current_tokens = 0

    for review in reviews:
        review_id = review['uid']
        review_text = review['text']
        review_rating = transform_rating_to_star_format(review['rating'])

        imp_tokens = num_tokens_from_string(review_text, encoding_name="cl100k_base")
        if current_tokens + imp_tokens + 1 <= max_tokens:
            current_batch.append((review_id,review_rating, review_text))
            current_tokens += imp_tokens + 1
        else:
            batches.append(current_batch)
            current_batch = [(review_id, review_rating, review_text)]
            current_tokens = imp_tokens
    if current_batch:
        batches.append(current_batch)

    return batches


def aggregate_all_categories(data):
    """
    Aggregate items from all products under the same broad groupings.

    Parameters:
    - data (list): List of dictionaries representing products/categories.

    Returns:
    - dict: Aggregated items under the broad groupings.
    """
    aggregated_results = {}
    try:
        for product in data:
            for category_name, items in product.items():
                if category_name not in aggregated_results:
                    aggregated_results[category_name] = []
                aggregated_results[category_name].extend(items)
    except Exception as e:
        logging.error(f"Error in aggregate_all_categories: {e}")
        return {}
    return aggregated_results





def quantify_category_data(inputData):
    processedData = {}
    
    for categoryKey, labels in inputData.items():
        categoryTotalObservations = sum([len(labelData['uid']) for labelData in labels])
        processedLabels = []
        
        for labelData in labels:
            labelObservations = len(labelData['uid'])
            
            # Check for zero total observations and calculate label percentage
            labelPercentage = (labelObservations / categoryTotalObservations) * 100 if categoryTotalObservations != 0 else 0
            formattedLabelPercentage = int("{:.0f}".format(labelPercentage))
            
            # Check for zero length and calculate average rating for label
            if len(labelData['rating']) != 0:
                averageRating = sum(labelData['rating']) / len(labelData['rating'])
                formattedAverageRating = float("{:.1f}".format(averageRating))
                
                processedLabelData = {
                    'label': labelData['label'],
                    'uid': labelData['uid'],
                    'asin': list(set(labelData['asin'])),
                    'numberOfObservations"': labelObservations,
                    'percentage': formattedLabelPercentage,
                    'rating': formattedAverageRating
                }
                
                processedLabels.append(processedLabelData)
            else:
                # Skip if no ratings
                continue
        
        processedData[categoryKey] = processedLabels
    
    return processedData
