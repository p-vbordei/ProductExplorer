# %% [markdown]
# #### STRUCTURE
# - Select required review data
#     - read csv
#     - clean reviews
#     - filter and sort reviews
#     - select the number of required reviews
# - Process review data with GPT
#     - describe prompts
#     - write tasks
#     - process tasks
# - Process resulting dictionary
#     - map results
#     - explode results to dataframe format
#     - save data
# 


#products (collection)
#|
#|- asin (document)
#|  |- details (field)
#|
#|- reviews (sub-collection)
#   |
#   |- review_id (document)
#      |- review fields (fields)




#investigations (collection)
#|- investigation_id (document)
#|  |- asins (field)
#|  |- investigation_status (field)
#|  |- investigation_status_timestamp (field)
#|  |- user_id (field)


# %%
import pandas as pd
import numpy as np
import re
import requests
import json
import csv
import openai
import time
import tiktoken
from typing import Dict

from rich.console import Console
from rich.table import Table
console = Console()
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if os.getenv("OPENAI_API_KEY") is not None:
    print ("OPENAI_API_KEY is ready")
else:
    print ("OPENAI_API_KEY environment variable not found")

GPT_MODEL = "gpt-3.5-turbo"
INVESTIGATION = "investigationId2"

from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials, firestore

# Firestore details
cred_path = '/Users/vladbordei/Documents/Development/ProductExplorer/notebooks/productexplorerdata-firebase-adminsdk-ulb3d-465f23dff3.json'

# Initialize Firestore
cred = credentials.Certificate(cred_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

#%%

############### ETL FUNCTIONS ###############

def initial_review_clean_data(df, limit=3000):
    # Add the asin column to the dataframe
    # df['asin'] = df['asin.original']

    # Process the reviews in the dataframe
    df.loc[:, 'review'] = df['review'].apply(clean_review)
    df.loc[:, 'num_tokens'] = df['review'].apply(num_tokens_from_string)
    df.loc[:, 'review'] = df.apply(lambda x: x['review'][:limit * 3] if x['num_tokens'] > limit else x['review'], axis=1)
    df.loc[:, 'review_num_tokens'] = df['review'].apply(num_tokens_from_string)

    return df

def num_tokens_from_string(string: str, encoding_name = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def clean_review(review_body):
    try:
        return re.sub(r'[^a-zA-Z0-9\s]+', '', review_body)
    except TypeError as e:
        print(f"Error cleaning review: {e}")
        return ""

def initial_review_clean_data(reviews_list, limit=3000):
    # Process the reviews in the list of dictionaries
    for review_dict in reviews_list:
        review_dict['review'] = clean_review(review_dict['review'])
        review_dict['num_tokens'] = num_tokens_from_string(review_dict['review'])
        if review_dict['num_tokens'] > limit:
            review_dict['review'] = review_dict['review'][:limit * 3]
        review_dict['review_num_tokens'] = num_tokens_from_string(review_dict['review'])
    return reviews_list


#%%

############### FIREBASE FUNCTIONS ###############

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


# %%



# #### THIS PART REDUCES THE REVIEW NUMBERS SO WE CAN TEST AT EASE
# 
# #### Select required review data
#     - clean reviews
#     - filter and sort reviews
#     - select the number of required reviews
# %%

update_investigation_status(INVESTIGATION, "started_reviews")
reviews_download = get_investigation_and_reviews(INVESTIGATION)


# %%

flattened_reviews = [item for sublist in reviews_download for item in sublist]

# %%
reviews_list = flattened_reviews.copy()
asins_list = []
review_ids_list = []
for review in reviews_list:
    review['asin_data'] = review['asin']
    review['asin'] = review['asin']['original']
    asins_list.append(review['asin'])
    review_ids_list.append(review['id'])

# %%
clean_reviews_list = initial_review_clean_data(reviews_list)


# %% [markdown]
# #### WRITING DOWN TASKS FOR AI TO PROCESS IN PARALLEL
# 
# #### Process review data with GPT
#     - review functions
# 
# https://towardsdatascience.com/an-introduction-to-openai-function-calling-e47e7cd7680e

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


# %% [markdown]
# #### Process review data with GPT. Run the model in async mode

# %%
import asyncio
import aiohttp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}"
}

class ProgressLog:
    def __init__(self, total):
        self.total = total
        self.done = 0

    def increment(self):
        self.done = self.done + 1

    def __repr__(self):
        return f"Done runs {self.done}/{self.total}."

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(20), before_sleep=print, retry_error_callback=lambda _: None)
async def get_completion(content, session, semaphore, progress_log, functions=None, function_call=None):
    async with semaphore:
        json_data = {
            "model": GPT_MODEL,
            "messages": content,
            "temperature": 0
        }
        
        if functions is not None:
            json_data.update({"functions": functions})
        if function_call is not None:
            json_data.update({"function_call": function_call})

        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=json_data) as resp:
            response_json = await resp.json()
            progress_log.increment()
            print(progress_log)
            return response_json["choices"][0]['message']

async def get_completion_list(content_list, max_parallel_calls, timeout, functions=None, function_call=None):
    semaphore = asyncio.Semaphore(value=max_parallel_calls)
    progress_log = ProgressLog(len(content_list))

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(timeout)) as session:
        return await asyncio.gather(*[get_completion(content, session, semaphore, progress_log, functions, function_call) for content in content_list])



# %%
# Define maximum parallel calls and timeout
max_parallel_calls = 100  # Adjust based on how many requests you want to make concurrently
timeout = 60  # Adjust timeout as per your needs

# Define functions and function call
functions = review_functions  # Replace with your functions
function_call = {"name": "review_data_function"}

# Create a list of messages for all reviews
content_list = []
for review_dict in clean_reviews_list:
    review = review_dict['review']
    messages = [
        {"role": "user", "content": f"REVIEW: ```{review}```"},
    ]
    content_list.append(messages)

# Wrap your main coroutine invocation in another async function.
async def main():
    responses = await get_completion_list(content_list, max_parallel_calls, timeout, functions, function_call)
    return responses

#####################
#%%
# Run the main coroutine
responses = await main()
#####################


# %%
# Evaluate responses and add them to clean_reviews_list
eval_responses = []
for i, item in enumerate(responses):
    data = item['function_call']['arguments']
    # Replace 'null' with 'None' in the data string before evaluation
    data = data.replace('null', 'None')
    eval_data = eval(data)
    eval_responses.append(eval_data)
    clean_reviews_list[i]['insights'] = eval_data

# Assuming that the new columns are the keys of the eval_response dictionaries
new_cols = list(clean_reviews_list[1]['insights'].keys())

# %%
# Add new columns to the dictionaries in clean_reviews_list
for review_dict in clean_reviews_list:
    for col in new_cols:
        try:
            review_dict[col] = review_dict['insights'][col]
        except:
            review_dict[col] = None
    review_dict.pop('insights')
    

# %%
# Replace 'asin_data' with 'asin' in the dictionaries in clean_reviews_list
for review_dict in clean_reviews_list:
    review_dict['asin'] = review_dict.pop('asin_data')


# %%
################# write to firestore #################

import time
from collections import defaultdict

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

# Call the function
write_reviews(clean_reviews_list)


# %%
################# ETL Part 2: Clustering#################
##########################################################

from openai.embeddings_utils import get_embedding
from sklearn.cluster import AgglomerativeClustering

import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt

# %%
reviews_df = pd.DataFrame(clean_reviews_list)

# %%
# drop useless columns
drop_columns_proposed = [ 'Verified', 'Helpful', 'Title', 'review','Videos','Variation', 'Style', 'num_tokens', 'review_num_tokens', 'review_data']
drop_columns = list(set(drop_columns_proposed).intersection(set(reviews_df.columns)))
reviews_df.drop(columns = drop_columns, inplace = True)

# %%
data_cols = ["Review Summary","Buyer Motivation", "Customer Expectations", "How the product is used", "Where the product is used", "User Description", "Packaging", "Season", "When the product is used", "Appraisal", "Quality", "Durability", "Ease of Use", "Setup and Instructions", "Noise and Smell", "Size and Fit", "Danger Appraisal", "Design and Appearance", "Parts and Components", "Issues"]
for col in data_cols:
    try:
        reviews_df[col] = reviews_df[col].fillna('')
        reviews_df[col].replace(['\n', 'not mentioned',np.nan, '',' ', 'NA', 'N/A', 'missing', 'NaN', 'unknown', 'Not mentioned','not specified','Not specified'], 'unknown', inplace = True)
    except:
        pass

# %%
columns_to_pivot = ["Buyer Motivation", "Customer Expectations", "How the product is used", "Where the product is used", "User Description", "Packaging", "Season", "When the product is used", "Appraisal", "Quality", "Durability", "Ease of Use", "Setup and Instructions", "Noise and Smell",  "Size and Fit", "Danger Appraisal", "Design and Appearance", "Parts and Components", "Issues"]

reviews_data_df = reviews_df.melt(id_vars=[col for col in reviews_df.columns if col not in columns_to_pivot], 
                    value_vars=columns_to_pivot, 
                    var_name='Attribute', 
                    value_name='Value')
#%%

try:
    df = reviews_data_df[reviews_data_df['Value'] != 'unknown']
except ValueError as e:
    if "cannot reindex on an axis with duplicate labels" in str(e):
        # Check for duplicate indexes
        if reviews_data_df.index.duplicated().any():
            print("Detected duplicate indexes. Resetting index...")
            reviews_data_df = reviews_data_df.reset_index(drop=True)
        
        # Check for duplicate columns
        if reviews_data_df.columns.duplicated().any():
            duplicate_columns = reviews_data_df.columns[reviews_data_df.columns.duplicated()].tolist()
            print(f"Detected duplicate columns: {duplicate_columns}. Renaming...")
            for col in duplicate_columns:
                reviews_data_df = reviews_data_df.rename(columns={col: col + '_duplicate'})
        
        # Retry the operation
        df = reviews_data_df[reviews_data_df['Value'] != 'unknown']
    else:
        # If the error is something else, you might want to raise it to handle it differently
        raise e


# %%

# %%
###################### Embedding  ######################

embedding_model = "text-embedding-ada-002"
embedding_encoding = "cl100k_base"  
max_tokens = 8000  
encoding = tiktoken.get_encoding(embedding_encoding)

async def get_embedding(text: str, model="text-embedding-ada-002") -> list[float]:
    async with aiohttp.ClientSession() as session:
        for attempt in range(6):  # Retry up to 6 times
            try:
                async with session.post(
                    'https://api.openai.com/v1/embeddings',
                    json={"input": [text], "model": model},
                    headers={'Authorization': f'Bearer {OPENAI_API_KEY}'}
                ) as response:
                    response = await response.json()
                    return np.array(response["data"][0]["embedding"])  # Convert embedding to numpy array directly
            except Exception as e:
                wait_time = random.uniform(1, min(20, 2 ** attempt))  # Exponential backoff
                print(f"Request failed with {e}, retrying in {wait_time} seconds.")
                await asyncio.sleep(wait_time)
        print("Failed to get embedding after 6 attempts, returning None.")
        return None


import nest_asyncio
nest_asyncio.apply()
async def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    loop = asyncio.get_event_loop()
    tasks = []

    # Filter rows by token count
    df["n_tokens"] = df['Value'].apply(lambda x: len(encoding.encode(x)))  # Assuming 'encoding' is defined
    df = df[df.n_tokens <= max_tokens]

    for index, row in df.iterrows():
        task = loop.create_task(get_embedding(row['Value'], model=embedding_model))
        tasks.append(task)

    df['embedding'] = await asyncio.gather(*tasks)
    return df

# omit reviews that are too long to embed
df["n_tokens"] = df['Value'].apply(lambda x: len(encoding.encode(x)))
df = df[df.n_tokens <= max_tokens]


# Use asyncio's run method to start the event loop and run process_dataframe
df = asyncio.run(process_dataframe(df))
df["embedding"] = df["embedding"].apply(np.array)  # convert string to numpy array

# %%
###################### Clustering  ######################

max_n_clusters = 2
df["cluster"] = np.nan

types_list = list(reviews_data_df['Attribute'].unique())

for type in types_list:
    print(type)
    df_type = df[df['Attribute'] == type]
    n_clusters = min(max_n_clusters, len(df_type['Value'].unique()))
    if n_clusters > 2:
        clustering = AgglomerativeClustering(n_clusters=n_clusters)
        matrix = np.vstack(df_type["embedding"].values)
        labels = clustering.fit_predict(matrix)
        df_type["cluster"] = labels
        df.loc[df['Attribute'] == type, "cluster"] = df_type["cluster"]
    else:
        df.loc[df['Attribute'] == type, "cluster"] = 0

df['cluster'] = df['cluster'].astype(int)
cluster_df  = df[['Attribute', 'cluster','Value']]
cluster_df.drop_duplicates(inplace = True)

# %%
###################### Labeling  ######################

labeling_function = [
    {
        "name": "cluster_label",
        "description": "Provide a single label for the topic represented in the list of values. ",
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


# Define maximum parallel calls and timeout
max_parallel_calls = 100  # Adjust based on how many requests you want to make concurrently
timeout = 60  # Adjust timeout as per your needs

# Define functions and function call
functions = labeling_function  # Replace with your functions
function_call = {"name": "cluster_label"}

# Initialize 'content_list' if it's not already defined
content_list = []

# Loop through the unique types in the 'Attribute' column of 'cluster_df'
for type in cluster_df['Attribute'].unique():
    # Filter 'cluster_df' to get only rows with the current 'type' and loop through the clusters for that type
    for cluster in cluster_df[cluster_df['Attribute'] == type]['cluster'].unique():
        # Get the unique values for the current 'type' and 'cluster'
        values = cluster_df[(cluster_df['Attribute'] == type) & (cluster_df['cluster'] == cluster)]['Value'].unique()
        # Create the message dictionary
        messages = [{"role": "user", "content": f"The value presented are part of {type}. Provide a single seven words label for this list of values : ```{values}```. "}]
        content_list.append(messages)

# Wrap your main coroutine invocation in another async function.
async def main():
    responses = await get_completion_list(content_list, max_parallel_calls, timeout, functions, function_call)
    return responses

# Now you can run your code using an await expression:
responses = await main()

# %%
########### Interpret the responses ###############

eval_responses = []
for item in responses:
    data = item['function_call']['arguments']
    eval_data = eval(data)
    eval_responses.append(eval_data['cluster_label'])

cluster_response_df= cluster_df.drop(columns = ['Value']).drop_duplicates()
cluster_response_df['cluster_label'] = eval_responses

df_with_clusters = df.merge(cluster_response_df, on = ['Attribute', 'cluster'], how = 'left')


# Drop some more columns
drop_columns_proposed = ['n_tokens', 'embedding','Date', 'Author','Images']
drop_columns = list(set(drop_columns_proposed).intersection(set(df_with_clusters.columns)))
df_with_clusters.drop(columns = drop_columns, inplace = True)

# %%
###############  Save results  ###############

merge_reviews_df = pd.DataFrame(clean_reviews_list)


merge_columns_proposed = ['review', 'name', 'date', 'asin', 'id', 'review_data', 'rating','title', 'media', 'verified_purchase', 'num_tokens','review_num_tokens',]
merge_columns = list(set(merge_columns_proposed).intersection(set(merge_reviews_df.columns)))
reviews_with_clusters = df_with_clusters.merge(merge_reviews_df[merge_columns], on = ['id'], how = 'left')


reviews_with_clusters_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/reviews_with_clusters.csv'
reviews_with_clusters.to_csv(reviews_with_clusters_path)

# %% [markdown]
# # Quantify observations

# %%
########## Investigation level data quanitification ############
df_with_clusters['asin'] = df_with_clusters['asin'].apply(lambda x: x['original'])

agg_result = df_with_clusters.groupby(['Attribute', 'cluster_label']).agg({
    'rating': lambda x: list(x),
    'id': lambda x: list(x),
    'asin': lambda x: list(x),
    }).reset_index()

# Aggregate the count separately
count_result = df_with_clusters.groupby(['Attribute', 'cluster_label']).size().reset_index(name='observation_count')
attribute_clusters_with_percentage = pd.merge(agg_result, count_result, on=['Attribute', 'cluster_label'])


# Calculate the average rating
m = []
for e in attribute_clusters_with_percentage['rating']:
    f =[]
    for r in e:
        f.append(int(r))
    m.append(np.mean(f))
k = []
for e in m:
    f = round(e,0)
    f = int(f)
    k.append(f)

attribute_clusters_with_percentage['rating_avg'] = k

# %%
############# Save Investigation Level Data Quantification #############
total_observations_per_attribute = df_with_clusters.groupby('Attribute').size()

attribute_clusters_with_percentage = attribute_clusters_with_percentage.set_index('Attribute')  # set 'Attribute' as the index to allow for division
attribute_clusters_with_percentage['percentage_of_observations_vs_total_number_per_attribute'] = attribute_clusters_with_percentage['observation_count'] / total_observations_per_attribute * 100
attribute_clusters_with_percentage = attribute_clusters_with_percentage.reset_index()  # reset the index if desired

number_of_reviews = reviews_with_clusters['id'].unique().shape[0]
number_of_reviews
attribute_clusters_with_percentage['percentage_of_observations_vs_total_number_of_reviews'] = attribute_clusters_with_percentage['observation_count'] / number_of_reviews * 100



attribute_clusters_with_percentage.head(3)


attribute_clusters_with_percentage_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/attribute_clusters_with_percentage.csv'
attribute_clusters_with_percentage.to_csv(attribute_clusters_with_percentage_path, index = False)

# %%
########## ASIN Level Data Quantification ############

# df_with_clusters['asin'] = df_with_clusters['asin'].apply(lambda x: x['original'])

# %%
agg_result = df_with_clusters.groupby(['Attribute', 'cluster_label', 'asin']).agg({
    'rating': lambda x: list(x),
    'id': lambda x: list(x),
}).reset_index()


# %%
# Aggregate the count separately
count_result = df_with_clusters.groupby(['Attribute', 'cluster_label', 'asin']).size().reset_index(name='observation_count')
attribute_clusters_with_percentage_by_asin = pd.merge(agg_result, count_result, on=['Attribute', 'cluster_label', 'asin'])

# Calculate the average rating
m = []
for e in attribute_clusters_with_percentage_by_asin['rating']:
    f = []
    for r in e:
        f.append(int(r))
    m.append(np.mean(f))
k = []
for e in m:
    f = round(e, 0)
    f = int(f)
    k.append(f)

attribute_clusters_with_percentage_by_asin['rating_avg'] = k



# %%
# Compute the total observations per attribute and asin
df_with_clusters['total_observations_per_attribute_asin'] = df_with_clusters.groupby(['Attribute', 'asin'])['asin'].transform('count')

# Calculate the percentage
attribute_clusters_with_percentage_by_asin['percentage_of_observations_vs_total_number_per_attribute'] = attribute_clusters_with_percentage_by_asin['observation_count'] / df_with_clusters['total_observations_per_attribute_asin'] * 100

number_of_reviews = reviews_with_clusters['id'].unique().shape[0]
attribute_clusters_with_percentage_by_asin['percentage_of_observations_vs_total_number_of_reviews'] = attribute_clusters_with_percentage_by_asin['observation_count'] / number_of_reviews * 100


# %%
attribute_clusters_with_percentage_by_asin.head(3)

# %%
attribute_clusters_with_percentage_by_asin_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/attribute_clusters_with_percentage_by_asin.csv'
attribute_clusters_with_percentage_by_asin.to_csv(attribute_clusters_with_percentage_by_asin_path, index = False)
# %%
