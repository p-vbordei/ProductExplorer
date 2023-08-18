# ##################
# reviews_processing.py
# %%

import os
import asyncio
import pandas as pd
import numpy as np

from sklearn.cluster import AgglomerativeClustering

from dotenv import load_dotenv
try:
    from src import app
    from src.reviews_data_processing_utils import process_datapoints
    from src.firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, save_cluster_info_to_firestore, write_insights_to_firestore
    from src.openai_utils import get_completion_list, process_dataframe_async_embedding
except ImportError:
    from reviews_data_processing_utils import process_datapoints
    from firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, save_cluster_info_to_firestore, write_insights_to_firestore
    from openai_utils import get_completion_list, process_dataframe_async_embedding


####################################### PROCESS REVIEWS WITH GPT #######################################

def process_reviews_with_gpt(reviewsList, OPENAI_API_KEY):
    reviewFunctions = [
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

    functions = reviewFunctions
    functionCall = {"name": "reviewDataFunction"}

    contentList = []
    for reviewDict in reviewsList:
        review = reviewDict['review']
        messages = [
            {"role": "user", "content": f"REVIEW: ```{review}```"},
        ]
        contentList.append(messages)

    async def main():
        responses = await get_completion_list(contentList, functions, functionCall)
        return responses

    responses = asyncio.run(main())

    evalResponses = []
    for i, item in enumerate(responses):
        data = item['functionCall']['arguments']
        data = data.replace('null', 'None')
        evalData = eval(data)

        evalResponses.append(evalData)
        reviewsList[i]['insights'] = evalData

    newCols = list(reviewsList[1]['insights'].keys())

    for reviewDict in reviewsList:
        for col in newCols:
            try:
                reviewDict[col] = reviewDict['insights'][col]
            except:
                reviewDict[col] = None
        reviewDict.pop('insights')

    for reviewDict in reviewsList:
        reviewDict['asin'] = reviewDict.pop('asinData')

    write_reviews_to_firestore(reviewsList)
    return reviewsList


######################################### CLUSTERING #########################################
# %%
def cluster_reviews(clean_reviews_list):
    # Convert reviews list to DataFrame
    reviews_df = pd.DataFrame(clean_reviews_list)

    # Drop unnecessary columns
    drop_columns = ['Verified', 'Helpful', 'Title', 'review', 'Videos', 'Variation', 'Style', 'num_tokens',
                     'review_num_tokens', 'review_data', 'title', 'date', 'verified_purchase', 
                     'name', 'media', 'rating', 'n_tokens']
    reviews_df = reviews_df.drop(columns=drop_columns, errors='ignore')

    # Fill missing values and replace undesired values
    data_cols = ["Review Summary", "Buyer Motivation", "Customer Expectations", 
                 "How the product is used", "Where the product is used", "User Description",
                 "Packaging", "Season", "When the product is used", "Appraisal", "Quality", "Durability", 
                 "Ease of Use", "Setup and Instructions", "Noise and Smell", "Size and Fit", 
                 "Danger Appraisal", "Design and Appearance", "Parts and Components", "Issues"]
    
    replace_values = ['\n', 'not mentioned', np.nan, '', ' ', 'NA', 'N/A', 'missing',
                      'NaN', 'unknown', 'Not mentioned', 'not specified', 'Not specified']
    
    for col in data_cols:
        reviews_df[col] = reviews_df[col].fillna('unknown').replace(replace_values, 'unknown')

    # Pivot the DataFrame
    columns_to_pivot = data_cols
    reviews_data_df = reviews_df.melt(id_vars=[col for col in reviews_df.columns if col not in columns_to_pivot], value_vars=columns_to_pivot, var_name='Attribute', value_name='Value')

    # Filter out 'unknown' values

    df = reviews_data_df.loc[reviews_data_df['Value'] != 'unknown']


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
    print(df.columns)

    if 'asin' in df.columns:
        df['asinOriginal'] = df['asin'].apply(lambda x: x['original'])
    else:
        print("'asin' column not found in df!")

    return df[['Attribute', 'cluster', 'Value', 'id', 'asinOriginal']].drop_duplicates()

# %%
############################################ CLUSTER LABELING ############################################

def label_clusters(cluster_df):
    # Define labeling function
    labeling_function = [
        {
            "name": "clusterLabel",
            "description": "Provide a single label for the topic represented in the list of values.",
            "parameters": {
                "type": "object",
                "properties": {
                    "clusterLabel": {
                        "type": "string",
                        "description": "Provide a single label for the topic represented in the list of values. [7 words]. Example: 'Low perceived quality versus competitors', 'the assembly kit breaks easily and often', 'the speaker has a low sound quality','the taste was better than expected'',' "
                    },
                },
                "required": ["clusterLabel"]
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
    responses = asyncio.run(get_completion_list(content_list, labeling_function, {"name": "clusterLabel"}))

    # Interpret the responses
    eval_responses = []
    for item in responses:
        data = item['function_call']['arguments']
        eval_data = eval(data)
        eval_responses.append(eval_data['clusterLabel'])

    # Create a DataFrame to hold unique combinations of 'Attribute' and 'cluster'
    cluster_response_df = cluster_df[['Attribute', 'cluster']]
    cluster_response_df.drop_duplicates(inplace=True)
    cluster_response_df.reset_index(inplace=True, drop=True)
    cluster_response_df['clusterLabel'] = eval_responses

    # Merge the cluster labels back to the main cluster_df
    df_with_clusters = cluster_df.merge(cluster_response_df, on=['Attribute', 'cluster'], how='left')
    drop_columns = ['n_tokens', 'embedding', 'Date', 'Author', 'Images']
    df_with_clusters = df_with_clusters.drop(columns=drop_columns, errors='ignore')

    return df_with_clusters

############################################ QUANTIFY OBSERVATIONS ############################################

def quantify_observations(reviewsWithClusters, cleanReviews):
    """Quantify observations at both the investigation and ASIN levels."""
    
    df_with_clusters = reviewsWithClusters.merge(pd.DataFrame(cleanReviews), left_on='id', right_on='id', how='left')

    agg_result = df_with_clusters.groupby(['Attribute', 'clusterLabel']).agg({
        'rating': lambda x: list(x),
        'id': lambda x: list(x),
        'asinOriginal': lambda x: list(x),
        }).reset_index()

    count_result = df_with_clusters.groupby(['Attribute', 'clusterLabel']).size().reset_index(name='observationCount')
    attribute_clusters_with_percentage = pd.merge(agg_result, count_result, on=['Attribute', 'clusterLabel'])

    m = [np.mean([int(r) for r in e]) for e in attribute_clusters_with_percentage['rating']]
    k = [int(round(e, 0)) for e in m]
    attribute_clusters_with_percentage['rating_avg'] = k

    total_observations_per_attribute = df_with_clusters.groupby('Attribute').size()
    attribute_clusters_with_percentage = attribute_clusters_with_percentage.set_index('Attribute')
    attribute_clusters_with_percentage['percentageOfObservationsVsTotalNumberPerAttribute'] = attribute_clusters_with_percentage['observationCount'] / total_observations_per_attribute * 100
    attribute_clusters_with_percentage = attribute_clusters_with_percentage.reset_index()

    number_of_reviews = reviewsWithClusters['id'].unique().shape[0]
    attribute_clusters_with_percentage['percentageOfObservationsVsTotalNumberOfReviews'] = attribute_clusters_with_percentage['observationCount'] / number_of_reviews * 100

    # Quantify observations at the ASIN level
    agg_result_asin = df_with_clusters.groupby(['Attribute', 'clusterLabel', 'asinOriginal']).agg({
        'rating': lambda x: list(x),
        'id': lambda x: list(x),
    }).reset_index()

    count_result_asin = df_with_clusters.groupby(['Attribute', 'clusterLabel', 'asinOriginal']).size().reset_index(name='observationCount')
    attribute_clusters_with_percentage_by_asin = pd.merge(agg_result_asin, count_result_asin, on=['Attribute', 'clusterLabel', 'asinOriginal'])

    m_asin = [np.mean([int(r) for r in e]) for e in attribute_clusters_with_percentage_by_asin['rating']]
    k_asin = [int(round(e, 0)) for e in m_asin]
    attribute_clusters_with_percentage_by_asin['rating_avg'] = k_asin

    df_with_clusters['total_observations_per_attribute_asin'] = df_with_clusters.groupby(['Attribute', 'asinOriginal'])['asinOriginal'].transform('count')
    attribute_clusters_with_percentage_by_asin['percentageOfObservationsVsTotalNumberPerAttribute'] = attribute_clusters_with_percentage_by_asin['observationCount'] / df_with_clusters['total_observations_per_attribute_asin'] * 100
    attribute_clusters_with_percentage_by_asin['percentageOfObservationsVsTotalNumberOfReviews'] = attribute_clusters_with_percentage_by_asin['observationCount'] / number_of_reviews * 100

    return attribute_clusters_with_percentage, attribute_clusters_with_percentage_by_asin



############################################ RUN ############################################


def run_reviews_investigation(investigationId):
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    CRED_PATH =  '/Users/vladbordei/Documents/Development/ProductExplorer/notebooks/productexplorerdata-firebase-adminsdk-ulb3d-465f23dff3.json'
    
    cred_path = CRED_PATH

    # Initialize Firestore
    db = initialize_firestore(cred_path)

    # Get clean reviews
    reviews = get_clean_reviews(investigationId, db)

    # Process reviews with GPT
    cleanReviews = process_reviews_with_gpt(reviews, OPENAI_API_KEY)

    # Cluster reviews
    cluster_df = cluster_reviews(cleanReviews)

    # Label clusters
    reviewsWithClusters = label_clusters(cluster_df)

    # Quantify observations
    attribute_clusters_with_percentage, attribute_clusters_with_percentage_by_asin = quantify_observations(reviewsWithClusters, cleanReviews)

    # Save results to Firestore
    save_cluster_info_to_firestore(attribute_clusters_with_percentage, attribute_clusters_with_percentage_by_asin, investigationId)

    # Process datapoints
    datapoints = list(set(attribute_clusters_with_percentage['Attribute']))
    datapointsDict = {}
    for att in datapoints:
        df = attribute_clusters_with_percentage[attribute_clusters_with_percentage['Attribute'] == att]
        datapoints_list = process_datapoints(df)
        datapointsDict[att] = datapoints_list

    # Write insights to Firestore
    write_insights_to_firestore(investigationId, datapointsDict)

if __name__ == "__main__":
    load_dotenv()
    INVESTIGATION = "investigationId2"
    run_reviews_investigation(INVESTIGATION)
