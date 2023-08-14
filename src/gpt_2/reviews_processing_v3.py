import os
import asyncio
import pandas as pd
import numpy as np

from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials, firestore

from sklearn.cluster import AgglomerativeClustering
from openai_utils import process_dataframe_async_embedding


from dotenv import load_dotenv
from data_processing_utils import initial_review_clean_data_list
from firebase_utils import update_investigation_status, get_investigation_and_reviews, write_reviews, save_results_to_firestore
from openai_utils import get_completion_list

def initialize_firestore(cred_path):
    """Initialize Firestore client."""
    cred = credentials.Certificate(cred_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    return db

def get_clean_reviews(investigation_id, db):
    """Retrieve and clean reviews."""
    update_investigation_status(investigation_id, "started_reviews")
    reviews_download = get_investigation_and_reviews(investigation_id)
    flattened_reviews = [item for sublist in reviews_download for item in sublist]
    for review in flattened_reviews:
        review['asin_data'] = review['asin']
        review['asin'] = review['asin']['original']
    return initial_review_clean_data_list(flattened_reviews)


####################################### PROCESS REVIEWS WITH GPT #######################################

def process_reviews_with_gpt(reviews_list, openai_api_key):
    review_functions = [
        {
            "name": "review_data_function",
            "description": "product description",
            "parameters": {
                "type": "object",
                "properties": {
                    "Review Summary": {
                        "type": "string",
                        "description": "A brief summary of the review. Eg: Good product overall, but improvements can be made in battery life and noise levels."
                    },
                    "Buyer Motivation": {
                        "type": "string",
                        "description": "Reasons why the buyer purchased the product. Eg: to replace an old product, to try out a new product, to give as a gift"
                    },
                    "Customer Expectations": {
                        "type": "string",
                        "description": "Expectations the customer had before purchasing the product. Eg: to be able to use the product for a long time, to be able to use the product in a variety of situations, to be able to use the product for a specific purpose"
                    },
                    "How the product is used": {
                        "type": "string",
                        "description": "Information about what the product is used for or about how the product is used. Eg: doodling, practicing letters/shapes, playing games"
                    },
                    "Where the product is used": {
                        "type": "string",
                        "description": "Suggested locations or situations where the product can be used. Eg: car, restaurant, garden, public parks"
                    },
                    "User Description": {
                        "type": "string",
                        "description": "Description of the user for the product. Eg: children, preschoolers,  basketball players, mothers, office workers"
                    },
                    "Packaging": {
                        "type": "string",
                        "description": "Description of the product's packaging. Eg: sturdy recyclable box, wrapped in plastic, great for gifting"
                    },
                    "Season": {
                        "type": "string",
                        "description": "Eg: fall and winter"
                    },
                    "When the product is used": {
                        "type": "string",
                        "description": "Time of day or week of use. Eg: early in the morning"
                    },
                    "Appraisal": {
                        "type": "string",
                        "description": "observations on price or value"
                    },
                    "Quality": {
                        "type": "string",
                        "description": "Observations on the quality. Eg: poor quality, great quality"
                    },
                    "Durability": {
                        "type": "string",
                        "description": "Observations on the durability. Eg: not durable, durable, very durable"
                    },
                    "Ease of Use": {
                        "type": "string",
                        "description": "Observations on the ease of use. Eg: not easy to use, easy to use"
                    },
                    "Setup and Instructions": {
                        "type": "string",
                        "description": "Observations on the setup. Eg: not easy to set up, easy to set up, easy to follow instructions,  not clear instructions"
                    },
                    "Noise and Smell": {
                        "type": "string",
                        "description": "Observations on the noise level or smell. Eg: too loud, quiet, squeaky, smells like roses, plastic smell"
                    },
                    "Size and Fit": {
                        "type": "string",
                        "description": "Observations on the fit. Eg: too tight, too loose, fits well, too small, too big"
                    },
                    "Danger Appraisal": {
                        "type": "string",
                        "description": "Observations on the safety of the product. Eg: dangerous, hazardous, safe, can break and harm, safe for children"
                    },
                    "Design and Appearance": {
                        "type": "string",
                        "description": "Observations on the design and appearance. Eg: not attractive, attractive, love the design, love the appearance"
                    },
                    "Parts and Components": {
                        "type": "string",
                        "description": "Observations on the parts and components. Eg: missing parts, all parts included, parts are easy to assemble"
                    },
                    "Issues": {
                        "type": "string",
                        "description": "If specified. Actionable observations on product problems to be addresed. Thorough detailing [max 100 words]. Eg: the product started to rust after one year, although I was expecting it to last 5 years before rusting."
                    },
                },
                "required": ["Review Summary","Buyer Motivation", "Customer Expectations", "How the product is used", "Where the product is used", "User Description", "Packaging", "Season", "When the product is used", "Price", "Quality", "Durability", "Ease of Use", "Setup and Instructions", "Noise and Smell", "Colors", "Size and Fit", "Danger Appraisal", "Design and Appearance", "Parts and Components", "Issues"]
            },
        }
    ]


    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    functions = review_functions
    function_call = {"name": "review_data_function"}

    content_list = []
    for review_dict in reviews_list:
        review = review_dict['review']
        messages = [
            {"role": "user", "content": f"REVIEW: ```{review}```"},
        ]
        content_list.append(messages)

    async def main():
        responses = await get_completion_list(content_list, functions, function_call)
        return responses

    responses = asyncio.run(main())

    eval_responses = []
    for i, item in enumerate(responses):
        data = item['function_call']['arguments']
        data = data.replace('null', 'None')
        eval_data = eval(data)

        eval_responses.append(eval_data)
        reviews_list[i]['insights'] = eval_data

    new_cols = list(reviews_list[1]['insights'].keys())

    for review_dict in reviews_list:
        for col in new_cols:
            try:
                review_dict[col] = review_dict['insights'][col]
            except:
                review_dict[col] = None
        review_dict.pop('insights')

    for review_dict in reviews_list:
        review_dict['asin'] = review_dict.pop('asin_data')

    write_reviews(reviews_list)
    return reviews_list


######################################### CLUSTERING #########################################

def cluster_reviews(clean_reviews_list):
    # Convert reviews list to DataFrame
    reviews_df = pd.DataFrame(clean_reviews_list)

    # Drop unnecessary columns
    drop_columns = ['Verified', 'Helpful', 'Title', 'review', 'Videos', 'Variation', 'Style', 'num_tokens', 'review_num_tokens', 'review_data']
    reviews_df = reviews_df.drop(columns=drop_columns, errors='ignore')

    # Fill missing values and replace undesired values
    data_cols = ["Review Summary", "Buyer Motivation", "Customer Expectations", "How the product is used", "Where the product is used", "User Description", "Packaging", "Season", "When the product is used", "Appraisal", "Quality", "Durability", "Ease of Use", "Setup and Instructions", "Noise and Smell", "Size and Fit", "Danger Appraisal", "Design and Appearance", "Parts and Components", "Issues"]
    replace_values = ['\n', 'not mentioned', np.nan, '', ' ', 'NA', 'N/A', 'missing', 'NaN', 'unknown', 'Not mentioned', 'not specified', 'Not specified']
    for col in data_cols:
        reviews_df[col] = reviews_df[col].fillna('unknown').replace(replace_values, 'unknown')

    # Pivot the DataFrame
    columns_to_pivot = data_cols
    reviews_data_df = reviews_df.melt(id_vars=[col for col in reviews_df.columns if col not in columns_to_pivot], value_vars=columns_to_pivot, var_name='Attribute', value_name='Value')

    # Filter out 'unknown' values
    df = reviews_data_df[reviews_data_df['Value'] != 'unknown']

    # Embedding
    df = asyncio.run(process_dataframe_async_embedding(df))

    # Clustering
    max_n_clusters = 2
    df["cluster"] = np.nan
    types_list = reviews_data_df['Attribute'].unique()
    for type in types_list:
        df_type = df[df['Attribute'] == type].copy()  # Explicitly create a copy
        n_clusters = min(max_n_clusters, len(df_type['Value'].unique()))
        if n_clusters > 1:
            clustering = AgglomerativeClustering(n_clusters=n_clusters)
            matrix = np.vstack(df_type["embedding"].values)
            labels = clustering.fit_predict(matrix)
            df_type["cluster"] = labels  # Modified assignment
            df.loc[df['Attribute'] == type, "cluster"] = df_type["cluster"]
        else:
            df.loc[df['Attribute'] == type, "cluster"] = 0

    df['cluster'] = df['cluster'].astype(int)
    return df[['Attribute', 'cluster', 'Value', 'id']].drop_duplicates()


############################################ CLUSTER LABELING ############################################

def label_clusters(cluster_df):
    # Define labeling function
    labeling_function = [
        {
            "name": "cluster_label",
            "description": "Provide a single label for the topic represented in the list of values.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cluster_label": {
                        "type": "string",
                        "description": "Provide a single label for the topic represented in the list of values. [7 words]. Example: 'Low perceived quality versus competitors', 'the assembly kit breaks easily and often', 'the speaker has a low sound quality','the taste was better than expected'',' "
                    },
                },
                "required": ["cluster_label"]
            },
        }
    ]

    # Prepare content list
    content_list = []
    for type in cluster_df['Attribute'].unique():
        for cluster in cluster_df[cluster_df['Attribute'] == type]['cluster'].unique():
            values = cluster_df[(cluster_df['Attribute'] == type) & (cluster_df['cluster'] == cluster)]['Value'].unique()
            messages = [{"role": "user", "content": f"The value presented are part of {type}. Provide a single label of seven words  for this list of values : ```{values}```. "}]
            content_list.append(messages)

    # Get responses
    responses = asyncio.run(get_completion_list(content_list, labeling_function, {"name": "cluster_label"}))

    # Interpret the responses
    eval_responses = []
    for item in responses:
        data = item['function_call']['arguments']
        eval_data = eval(data)
        eval_responses.append(eval_data['cluster_label'])

    # Create a DataFrame to hold unique combinations of 'Attribute' and 'cluster'
    cluster_response_df = cluster_df[['Attribute', 'cluster']]
    cluster_response_df.drop_duplicates(inplace=True)
    cluster_response_df.reset_index(inplace=True, drop=True)
    cluster_response_df['cluster_label'] = eval_responses

    # Merge the cluster labels back to the main cluster_df
    df_with_clusters = cluster_df.merge(cluster_response_df, on=['Attribute', 'cluster'], how='left')
    drop_columns = ['n_tokens', 'embedding', 'Date', 'Author', 'Images']
    df_with_clusters = df_with_clusters.drop(columns=drop_columns, errors='ignore')
    
    return df_with_clusters




############################################ QUANTIFY OBSERVATIONS ############################################

def quantify_observations(df_with_clusters, reviews_with_clusters, investigation_id):
    """Quantify observations at both the investigation and ASIN levels."""
    try:
        print(df_with_clusters.columns)
    except:
        pass

    try:
        print(df_with_clusters['asin'])
    except:
        pass

    # Check if 'asin' column exists in df_with_clusters
    if 'asin' in df_with_clusters.columns:
        df_with_clusters['asin'] = df_with_clusters['asin'].apply(lambda x: x['original'])
    else:
        print("'asin' column not found in df_with_clusters!")
        return  # Exit the function
    
    agg_result = df_with_clusters.groupby(['Attribute', 'cluster_label']).agg({
        'rating': lambda x: list(x),
        'id': lambda x: list(x),
        'asin': lambda x: list(x),
        }).reset_index()

    count_result = df_with_clusters.groupby(['Attribute', 'cluster_label']).size().reset_index(name='observation_count')
    attribute_clusters_with_percentage = pd.merge(agg_result, count_result, on=['Attribute', 'cluster_label'])

    m = [np.mean([int(r) for r in e]) for e in attribute_clusters_with_percentage['rating']]
    k = [int(round(e, 0)) for e in m]
    attribute_clusters_with_percentage['rating_avg'] = k

    total_observations_per_attribute = df_with_clusters.groupby('Attribute').size()
    attribute_clusters_with_percentage = attribute_clusters_with_percentage.set_index('Attribute')
    attribute_clusters_with_percentage['percentage_of_observations_vs_total_number_per_attribute'] = attribute_clusters_with_percentage['observation_count'] / total_observations_per_attribute * 100
    attribute_clusters_with_percentage = attribute_clusters_with_percentage.reset_index()

    number_of_reviews = reviews_with_clusters['id'].unique().shape[0]
    attribute_clusters_with_percentage['percentage_of_observations_vs_total_number_of_reviews'] = attribute_clusters_with_percentage['observation_count'] / number_of_reviews * 100

    # Quantify observations at the ASIN level
    agg_result_asin = df_with_clusters.groupby(['Attribute', 'cluster_label', 'asin']).agg({
        'rating': lambda x: list(x),
        'id': lambda x: list(x),
    }).reset_index()

    count_result_asin = df_with_clusters.groupby(['Attribute', 'cluster_label', 'asin']).size().reset_index(name='observation_count')
    attribute_clusters_with_percentage_by_asin = pd.merge(agg_result_asin, count_result_asin, on=['Attribute', 'cluster_label', 'asin'])

    m_asin = [np.mean([int(r) for r in e]) for e in attribute_clusters_with_percentage_by_asin['rating']]
    k_asin = [int(round(e, 0)) for e in m_asin]
    attribute_clusters_with_percentage_by_asin['rating_avg'] = k_asin

    df_with_clusters['total_observations_per_attribute_asin'] = df_with_clusters.groupby(['Attribute', 'asin'])['asin'].transform('count')
    attribute_clusters_with_percentage_by_asin['percentage_of_observations_vs_total_number_per_attribute'] = attribute_clusters_with_percentage_by_asin['observation_count'] / df_with_clusters['total_observations_per_attribute_asin'] * 100
    attribute_clusters_with_percentage_by_asin['percentage_of_observations_vs_total_number_of_reviews'] = attribute_clusters_with_percentage_by_asin['observation_count'] / number_of_reviews * 100

    print("------------ attributeclusters columns----------------------------")       
    print(attribute_clusters_with_percentage_by_asin.columns)
    save_clusters_to_firestore(investigation_id, attribute_clusters_with_percentage, attribute_clusters_with_percentage_by_asin)



############################################


def run(investigation_id, openai_api_key, cred_path):
    db = initialize_firestore(CRED_PATH)
    reviews = get_clean_reviews(investigation_id, db)
    clean_reviews = process_reviews_with_gpt(reviews, OPENAI_API_KEY)
    cluster_df = clustering(clean_reviews)
    reviews_with_clusters = cluster_labeling(cluster_df)
    save_results_to_firestore(df_with_clusters, clean_reviews_list)
    quantify_observations(cluster_df, reviews_with_clusters, investigation_id)

if __name__ == "__main__":
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    CRED_PATH =  '/Users/vladbordei/Documents/Development/ProductExplorer/notebooks/productexplorerdata-firebase-adminsdk-ulb3d-465f23dff3.json'
    INVESTIGATION = "investigationId2"

    run(INVESTIGATION, OPENAI_API_KEY, CRED_PATH)
