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

# %%
import pandas as pd
import numpy as np
import re
import requests
import json
import csv
import openai

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
investigation = "investigationId2"

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
    product_ref = db.collection('products').document(asin)
    reviews_from_firestore = product_ref.get()

    if reviews_from_firestore.exists:
        product_reviews= reviews_from_firestore.get('reviews')
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


# #### THIS PART REDUCES THE REVIEW NUMBERS SO WE CAN TEST AT EASE
# 
# #### Select required review data
#     - clean reviews
#     - filter and sort reviews
#     - select the number of required reviews
# %%

update_investigation_status(investigation, "started_reviews")
reviews_download = get_investigation_and_reviews(investigation)

flattened_reviews = [item for sublist in reviews_download for item in sublist]
reviews_list = flattened_reviews
for review in reviews_list:
    review['asin_data'] = review['asin']
    review['asin'] = review['asin']['original']


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
                "Value": {
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
    clean_reviews_list[i]['eval_response'] = eval_data

# Assuming that the new columns are the keys of the eval_response dictionaries
new_cols = list(clean_reviews_list[1]['eval_response'].keys())

# %%
# Add new columns to the dictionaries in clean_reviews_list
for review_dict in clean_reviews_list:
    for col in new_cols:
        try:
            review_dict[col] = review_dict['eval_response'][col]
        except:
            review_dict[col] = None

# Replace 'asin_data' with 'asin' in the dictionaries in clean_reviews_list
for review_dict in clean_reviews_list:
    review_dict['asin'] = review_dict.pop('asin_data')


# %%
# Write to firestore
import logging
for review_dict in clean_reviews_list:
    # extract review_id
    review_id = review_dict['id']
    # create a reference to the document location
    doc_ref = db.collection('reviews').document(str(review_id))
    try:
        # use set() with merge=True to update or create a new document
        doc_ref.set(review_dict, merge=True)  
        logging.info(f"Successfully saved/updated review with id {review_id}")
    except Exception as e:
        logging.error(f"Error saving/updating review with id {review_id}: {e}", exc_info=True)

update_investigation_status(investigation, "finished_reviews_extraction")
#%%

# NU PARE CA FAC UPDATE CORECT A DATELOR IN FIRESTORE. DE TESTAT IN CONTINUARE