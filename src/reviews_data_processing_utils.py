##########################
# data_processing_utils.py

import re
from tiktoken import get_encoding
import logging
logging.basicConfig(level=logging.INFO)
import numpy as np
import pandas as pd

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
        df_with_clusters = reviewsWithClusters.merge(pd.DataFrame(cleanReviews), left_on='id', right_on='id', how='left')
        
        # Debugging Step 2: Log NaN values
        logging.info(f"Number of NaN values in 'asin' column: {df_with_clusters['asin'].isna().sum()}")
        
        # Debugging Step 3: Log data types
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