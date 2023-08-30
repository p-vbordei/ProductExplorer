# ##################
# reviews_processing.py
# %%

import os
import asyncio
import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
import logging

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

def process_reviews_with_gpt(reviewsList, db):
    reviewFunctions = [
        {
            "name": "reviewDataFunction",
            "description": "product description",
            "parameters": {
                "type": "object",
                "properties": {
                    "reviewSummary": {
                        "type": "string",
                        "description": "A brief summary of the review. Eg: Good product overall, but improvements can be made in battery life and noise levels."
                    },
                    "buyerMotivation": {
                        "type": "string",
                        "description": "Reasons why the buyer purchased the product. Eg: to replace an old product, to try out a new product, to give as a gift"
                    },
                    "customerExpectations": {
                        "type": "string",
                        "description": "Expectations the customer had before purchasing the product. Eg: to be able to use the product for a long time, to be able to use the product in a variety of situations, to be able to use the product for a specific purpose"
                    },
                    "howTheProductIsUsed": {
                        "type": "string",
                        "description": "Information about what the product is used for or about how the product is used. Eg: doodling, practicing letters/shapes, playing games"
                    },
                    "whereTheProductIsUsed": {
                        "type": "string",
                        "description": "Suggested locations or situations where the product can be used. Eg: car, restaurant, garden, public parks"
                    },
                    "userDescription": {
                        "type": "string",
                        "description": "Description of the user for the product. Eg: children, preschoolers, basketball players, mothers, office workers"
                    },
                    "packaging": {
                        "type": "string",
                        "description": "Description of the product's packaging. Eg: sturdy recyclable box, wrapped in plastic, great for gifting"
                    },
                    "season": {
                        "type": "string",
                        "description": "Eg: fall and winter"
                    },
                    "whenTheProductIsUsed": {
                        "type": "string",
                        "description": "Time of day or week of use. Eg: early in the morning"
                    },
                    "appraisal": {
                        "type": "string",
                        "description": "observations on price or value"
                    },
                    "quality": {
                        "type": "string",
                        "description": "Observations on the quality. Eg: poor quality, great quality"
                    },
                    "durability": {
                        "type": "string",
                        "description": "Observations on the durability. Eg: not durable, durable, very durable"
                    },
                    "easeOfUse": {
                        "type": "string",
                        "description": "Observations on the ease of use. Eg: not easy to use, easy to use"
                    },
                    "setupAndInstructions": {
                        "type": "string",
                        "description": "Observations on the setup. Eg: not easy to set up, easy to set up, easy to follow instructions, not clear instructions"
                    },
                    "noiseAndSmell": {
                        "type": "string",
                        "description": "Observations on the noise level or smell. Eg: too loud, quiet, squeaky, smells like roses, plastic smell"
                    },
                    "sizeAndFit": {
                        "type": "string",
                        "description": "Observations on the fit. Eg: too tight, too loose, fits well, too small, too big"
                    },
                    "dangerAppraisal": {
                        "type": "string",
                        "description": "Observations on the safety of the product. Eg: dangerous, hazardous, safe, can break and harm, safe for children"
                    },
                    "designAndAppearance": {
                        "type": "string",
                        "description": "Observations on the design and appearance. Eg: not attractive, attractive, love the design, love the appearance"
                    },
                    "partsAndComponents": {
                        "type": "string",
                        "description": "Observations on the parts and components. Eg: missing parts, all parts included, parts are easy to assemble"
                    },
                    "issues": {
                        "type": "string",
                        "description": "If specified. Actionable observations on product problems to be addressed. Thorough detailing [max 100 words]. Eg: the product started to rust after one year, although I was expecting it to last 5 years before rusting."
                    },
                },
                "required": ["reviewSummary", "buyerMotivation", "customerExpectations", "howTheProductIsUsed", "whereTheProductIsUsed", "userDescription", "packaging", "season", "whenTheProductIsUsed", "price", "quality", "durability", "easeOfUse", "setupAndInstructions", "noiseAndSmell", "colors", "sizeAndFit", "dangerAppraisal", "designAndAppearance", "partsAndComponents", "issues"]
            },
        }
    ]

    functions = reviewFunctions
    function_call = {"name": "reviewDataFunction"}

    contentList = []
    for reviewDict in reviewsList:
        review = reviewDict['review']
        messages = [
            {"role": "user", "content": f"REVIEW: ```{review}```"},
        ]
        contentList.append(messages)

    async def main():
        responses = await get_completion_list(contentList, functions, function_call)
        return responses

    responses = asyncio.run(main())

    evalResponses = []
    for i, item in enumerate(responses):
        data = item['function_call']['arguments']
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

    write_reviews_to_firestore(reviewsList, db)
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
    dataCols = ["reviewSummary", "buyerMotivation", "customerExpectations", 
                "howTheProductIsUsed", "whereTheProductIsUsed", "userDescription",
                "packaging", "season", "whenTheProductIsUsed", "appraisal", "quality", "durability", 
                "easeOfUse", "setupAndInstructions", "noiseAndSmell", "sizeAndFit", 
                "dangerAppraisal", "designAndAppearance", "partsAndComponents", "issues"]

    
    replace_values = ['\n', 'not mentioned', np.nan, '', ' ', 'NA', 'N/A', 'missing',
                      'NaN', 'unknown', 'Not mentioned', 'not specified', 'Not specified']
    
    for col in dataCols:
        reviews_df[col] = reviews_df[col].fillna('unknown').replace(replace_values, 'unknown')

    # Pivot the DataFrame
    columnsToPivot = dataCols
    reviewsDataDf = reviews_df.melt(id_vars=[col for col in reviews_df.columns if col not in columnsToPivot], value_vars=columnsToPivot, var_name='attribute', value_name='Value')

    # Filter out 'unknown' values

    df = reviewsDataDf.loc[reviewsDataDf['Value'] != 'unknown']


    # Embedding
    df = asyncio.run(process_dataframe_async_embedding(df))

    # Clustering
    max_n_clusters = 2
    df["cluster"] = np.nan
    types_list = reviewsDataDf['attribute'].unique()
    for type in types_list:
        df_type = df[df['attribute'] == type].copy()  # Explicitly create a copy
        n_clusters = min(max_n_clusters, len(df_type['Value'].unique()))
        if n_clusters > 1:
            clustering = AgglomerativeClustering(n_clusters=n_clusters)
            matrix = np.vstack(df_type["embedding"].values)
            labels = clustering.fit_predict(matrix)
            df_type["cluster"] = labels  # Modified assignment
            df.loc[df['attribute'] == type, "cluster"] = df_type["cluster"]
        else:
            df.loc[df['attribute'] == type, "cluster"] = 0

    df['cluster'] = df['cluster'].astype(int)
    print(df.columns)


    return df[['attribute', 'cluster', 'Value', 'id', 'asin']].drop_duplicates()

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
    for type in cluster_df['attribute'].unique():
        for cluster in cluster_df[cluster_df['attribute'] == type]['cluster'].unique():
            values = cluster_df[(cluster_df['attribute'] == type) & (cluster_df['cluster'] == cluster)]['Value'].unique()
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

    # Create a DataFrame to hold unique combinations of 'attribute' and 'cluster'
    cluster_response_df = cluster_df[['attribute', 'cluster']]
    cluster_response_df.drop_duplicates(inplace=True)
    cluster_response_df.reset_index(inplace=True, drop=True)
    cluster_response_df['clusterLabel'] = eval_responses



    # Merge the cluster labels back to the main cluster_df
    df_with_clusters = cluster_df.merge(cluster_response_df, on=['attribute', 'cluster'], how='left')
    drop_columns = ['n_tokens', 'embedding', 'Date', 'Author', 'Images']
    df_with_clusters = df_with_clusters.drop(columns=drop_columns, errors='ignore')

    return df_with_clusters

############################################ QUANTIFY OBSERVATIONS ############################################

def quantify_observations(reviewsWithClusters, cleanReviews):
    """Quantify observations at both the investigation and ASIN levels."""
    
    df_with_clusters = reviewsWithClusters.merge(pd.DataFrame(cleanReviews), left_on='id', right_on='id', how='left')
    
    print(reviewsWithClusters.columns)
    print(pd.DataFrame(cleanReviews).columns)
    
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



############################################ RUN ############################################

# %%


def run_reviews_investigation(investigationId):
    try:
        # Initialize Firestore
        db = initialize_firestore()
    except Exception as e:
        logging.error(f"Error initializing Firestore: {e}")
        return

    try:
        # Get clean reviews
        reviews = get_clean_reviews(investigationId, db)
    except Exception as e:
        logging.error(f"Error getting clean reviews: {e}")
        return

    try:
        # Process reviews with GPT
        cleanReviews = process_reviews_with_gpt(reviews, db)
    except Exception as e:
        logging.error(f"Error processing reviews with GPT: {e}")
        return

    try:
        # Cluster reviews
        cluster_df = cluster_reviews(cleanReviews)
    except Exception as e:
        logging.error(f"Error clustering reviews: {e}")
        return

    try:
        # Label clusters
        reviewsWithClusters = label_clusters(cluster_df)
    except Exception as e:
        logging.error(f"Error labeling clusters: {e}")
        return

    try:
        # Quantify observations
        attributeClustersWithPercentage, attributeClustersWithPercentageByAsin = quantify_observations(reviewsWithClusters, cleanReviews)
    except Exception as e:
        logging.error(f"Error quantifying observations: {e}")
        return

    try:
        # Save results to Firestore
        save_cluster_info_to_firestore(attributeClustersWithPercentage, attributeClustersWithPercentageByAsin, investigationId, db)
    except Exception as e:
        logging.error(f"Error saving cluster info to Firestore: {e}")
        return

    try:
        # Process datapoints
        datapoints = list(set(attributeClustersWithPercentage['attribute']))
        datapointsDict = {}
        for att in datapoints:
            df = attributeClustersWithPercentage[attributeClustersWithPercentage['attribute'] == att]
            datapoints_list = process_datapoints(df)
            datapointsDict[att] = datapoints_list
    except Exception as e:
        logging.error(f"Error processing datapoints: {e}")
        return

    try:
        # Write insights to Firestore
        write_insights_to_firestore(investigationId, datapointsDict, db)
    except Exception as e:
        logging.error(f"Error writing insights to Firestore: {e}")
        return

    logging.info(f"Reviews investigation for {investigationId} completed successfully.")


# %%