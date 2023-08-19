# data_processing_utils.py

import os
import re
from tiktoken import get_encoding


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


def process_datapoints(df):
    datapoints_list = []
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