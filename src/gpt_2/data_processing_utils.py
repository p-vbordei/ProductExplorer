# data_processing_utils.py

import os
import re
from tiktoken import get_encoding
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def num_tokens_from_string(string: str, encoding_name="cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = get_encoding(encoding_name)
    return len(encoding.encode(string))

def clean_review(review_body):
    try:
        return re.sub(r'[^a-zA-Z0-9\s]+', '', review_body)
    except TypeError as e:
        print(f"Error cleaning review: {e}")
        return ""

def initial_review_clean_data(df, limit=3000):
    df.loc[:, 'review'] = df['review'].apply(clean_review)
    df.loc[:, 'num_tokens'] = df['review'].apply(num_tokens_from_string)
    df.loc[:, 'review'] = df.apply(lambda x: x['review'][:limit * 3] if x['num_tokens'] > limit else x['review'], axis=1)
    df.loc[:, 'review_num_tokens'] = df['review'].apply(num_tokens_from_string)
    return df

def initial_review_clean_data_list(reviews_list, limit=3000):
    for review_dict in reviews_list:
        review_dict['review'] = clean_review(review_dict['review'])
        review_dict['num_tokens'] = num_tokens_from_string(review_dict['review'])
        if review_dict['num_tokens'] > limit:
            review_dict['review'] = review_dict['review'][:limit * 3]
        review_dict['review_num_tokens'] = num_tokens_from_string(review_dict['review'])
    return reviews_list

def process_data_for_positives(df):
    # Process data for Positives, Pain Points, Buyer Motivation, and Customer Expectations
    positives_list = []
    for index, row in df.iterrows():
        data = {
            "Attribute": row["Attribute"],
            "Attribute Value": row["Value"],
            "Percentage of Count on Attribute Value vs. Count on Attribute": # Calculate percentage,
            "Additional Details on Attribute Value": # Extract or compute details
        }
        positives_list.append(data)
    return positives_list

def process_data_for_who(df):
    # Process data for Who, What, Where, and When
    who_list = []
    for index, row in df.iterrows():
        data = {
            "Attribute": row["Attribute"],
            "Attribute Value": row["Value"],
            "Count of Observations of Attribute Value": # Count observations,
            "Count of Observations of Attribute": # Count observations
        }
        who_list.append(data)
    return who_list

def process_data_for_feature_importance(df):
    # Process data for Feature Importance
    feature_importance_list = []
    for index, row in df.iterrows():
        data = {
            "Attribute": row["Attribute"],
            "Attribute Value": row["Value"],
            "Attribute Rating Average": # Calculate average,
            "Attribute Value Percentage of Total Reviews": # Calculate percentage
        }
        feature_importance_list.append(data)
    return feature_importance_list

def save_to_firestore(investigation_id, positives, who, feature_importance):
    # Save processed data to Firestore
    doc_ref = db.collection('Insights').document(investigation_id)
    doc_ref.set({
        "Positives": positives,
        "Who": who,
        "Feature Importance": feature_importance
    })