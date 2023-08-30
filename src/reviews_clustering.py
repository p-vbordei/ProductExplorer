######################################### CLUSTERING #########################################
# reviews_clustering.py

import pandas as pd
import numpy as np
import asyncio
from sklearn.cluster import AgglomerativeClustering
import logging

try:
    from src.openai_utils import get_completion_list, process_dataframe_async_embedding
except ImportError:
    from openai_utils import get_completion_list, process_dataframe_async_embedding

def cluster_reviews(clean_reviews_list):
    try:
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

    except Exception as e:
        logging.error(f"Error in cluster_reviews: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error


# %%
############################################ CLUSTER LABELING ############################################

import asyncio
import logging

def label_clusters(cluster_df):
    try:
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

    except Exception as e:
        logging.error(f"Error in label_clusters: {e}")
        return None  # Return None in case of error

# =====================