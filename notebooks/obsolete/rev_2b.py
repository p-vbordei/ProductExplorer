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
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')
WOLFRAM_ALPHA_APPID = os.getenv('WOLFRAM_ALPHA_APPID')
PROMPTLAYER_API_KEY = os.getenv('PROMPTLAYER_API_KEY')
HUGGINGFACEHUB_API_TOKEN = os.getenv('HUGGINGFACEHUB_API_TOKEN')

if os.getenv("OPENAI_API_KEY") is not None:
    print ("OPENAI_API_KEY is ready")
else:
    print ("OPENAI_API_KEY environment variable not found")

# from getpass import getpass
# HUGGINGFACEHUB_API_TOKEN = getpass()


GPT_MODEL = "gpt-3.5-turbo"

# %%
def num_tokens_from_string(string: str, encoding_name = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


# %%
def extract_asin(url):
    pattern = r'ASIN=(\w{10})'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        return None

def clean_review(review):
    try:
        return re.sub(r'[^a-zA-Z0-9\s]+', '', review)
    except TypeError as e:
        print(f"Error cleaning review: {e}")
        return ""



def initial_review_clean_data(df, limit=3000):
    # Add the asin column to the dataframe
    # df['asin'] = df['asin.original']

    # Process the reviews in the dataframe
    df.loc[:, 'review'] = df['review'].apply(clean_review)
    df.loc[:, 'num_tokens'] = df['review'].apply(num_tokens_from_string)
    df.loc[:, 'review'] = df.apply(lambda x: x['review'][:limit * 3] if x['num_tokens'] > limit else x['review'], axis=1)
    df.loc[:, 'review_num_tokens'] = df['review'].apply(num_tokens_from_string)

    return df



# %%
#asin_list_path = './data/external/asin_list.csv'
asin_list_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/external/asin_list.csv'
asin_list = pd.read_csv(asin_list_path)['asin'].tolist()

# %%
# reviews_path = './data/interim/reviews_with_sentiment.csv'
reviews_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/reviews_with_sentiment.csv'
reviews = pd.read_csv(reviews_path)

# %% [markdown]
# #### THIS PART REDUCES THE REVIEW NUMBERS SO WE CAN TEST AT EASE
# 
# #### Select required review data
#     - read csv
#     - clean reviews
#     - filter and sort reviews
#     - select the number of required reviews

# %%
# reviews.rename(columns={'Variation': 'asin'}, inplace=True)

# %%
reviews['asin'] = reviews['URL'].apply(extract_asin)

# %%
# Get the value counts for each unique value of 'asin.original'
counts = reviews['asin'].value_counts()

# Keep only the top values
top = counts.head(1000)

# Filter the reviews DataFrame to keep only rows with asin.original in the top 10
reviews_filtered = reviews[reviews['asin'].isin(top.index)]

# Get the datetime object for 12 months ago
date_12_months_ago = datetime.today() - timedelta(days=365)

# Convert the 'Date_initial' column to datetime format
reviews_filtered['Date'] = pd.to_datetime(reviews_filtered['Date'].apply(lambda s: s.split(' on ')[-1]))

# Convert the 'date.date' column to datetime format
reviews_filtered['Date'] = pd.to_datetime(reviews_filtered['Date'])

# Filter the reviews dataframe to only include reviews from the last 12 months
reviews_last_12_months = reviews_filtered[reviews_filtered['Date'] >= date_12_months_ago]

# keep only latest  x reviews
reviews_count_filtered = reviews_last_12_months.groupby('asin').tail(30)

# reset index
reviews_count_filtered = reviews_count_filtered.reset_index(drop=True)
reviews_count_filtered["id"] = reviews_count_filtered.index


# %%
reviews_df = initial_review_clean_data(reviews_count_filtered)

# %%
try:
    reviews_df.drop(columns = ["index", "level_0", "Author"], inplace = True)
except:
    pass

# %% [markdown]
# #### WRITING DOWN TASKS FOR AI TO PROCESS IN PARALLEL
# 
# #### Process review data with GPT
#     - review functions
# 

# %%
# https://towardsdatascience.com/an-introduction-to-openai-function-calling-e47e7cd7680e
review_functions = [
    {
        "name": "review_data_function",
        "description": "Provide a detailed description of a product",
        "parameters": {
            "type": "object",
            "properties": {
                "Review Summary": {
                    "type": "string",
                    "description": "A brief summary of the review. Example: Good product overall, but improvements can be made in battery life and noise levels."
                },
                "Buyer Motivation": {
                    "type": "string",
                    "description": "Reasons why the buyer purchased the product. Example: to replace an old product, to try out a new product, to give as a gift"
                },
                "Customer Expectations": {
                    "type": "string",
                    "description": "Expectations the customer had before purchasing the product. Example: to be able to use the product for a long time, to be able to use the product in a variety of situations, to be able to use the product for a specific purpose"
                },
                "How the product is used": {
                    "type": "string",
                    "description": "Information about what the product is used for or about how the product is used. Example: doodling, practicing letters/shapes, playing games"
                },
                "Where the product is used": {
                    "type": "string",
                    "description": "Suggested locations or situations where the product can be used. Example: car, restaurant, garden, public parks"
                },
                "User Description": {
                    "type": "string",
                    "description": "Description of the user for the product. Example: children, preschoolers,  basketball players, mothers, office workers"
                },
                "Packaging": {
                    "type": "string",
                    "description": "Description of the product's packaging. Example: sturdy recyclable box, wrapped in plastic, great for gifting"
                },
                "Season": {
                    "type": "string",
                    "description": "Season or time of year when the product is typically used. Example: fall and winter"
                },
                "When the product is used": {
                    "type": "string",
                    "description": "Time of day or week when the product is typically used. Example: early in the morning, in the weekend"
                },
                "Price": {
                    "type": "string",
                    "description": "Observations on the price. Example: not worth the price, good value for the price, great price"
                },
                "Quality": {
                    "type": "string",
                    "description": "Observations on the quality. Example: poor quality, great quality"
                },
                "Durability": {
                    "type": "string",
                    "description": "Observations on the durability. Example: not durable, durable, very durable"
                },
                "Ease of Use": {
                    "type": "string",
                    "description": "Observations on the ease of use. Example: not easy to use, easy to use"
                },
                "Setup and Instructions": {
                    "type": "string",
                    "description": "Observations on the setup. Example: not easy to set up, easy to set up, easy to follow instructions,  not clear instructions"
                },
                "Noise and Smell": {
                    "type": "string",
                    "description": "Observations on the noise level or smell. Example: too loud, quiet, squeaky, smells like roses, plastic smell"
                },
                "Colors": {
                    "type": "string",
                    "description": "Observations on the colors. Example: not enough color options, great color options, love the red"
                },
                "Size and Fit": {
                    "type": "string",
                    "description": "Observations on the fit. Example: too tight, too loose, fits well, too small, too big"
                },
                "Danger Appraisal": {
                    "type": "string",
                    "description": "Observations on the safety of the product. Example: dangerous, hazardous, safe, can break and harm, safe for children"
                },
                "Design and Appearance": {
                    "type": "string",
                    "description": "Observations on the design and appearance. Example: not attractive, attractive, love the design, love the appearance"
                },
                "Parts and Components": {
                    "type": "string",
                    "description": "Observations on the parts and components. Example: missing parts, all parts included, parts are easy to assemble"
                },
                "Issues": {
                    "type": "string",
                    "description": "If specified. Actionable observations on product problems to be addresed. Thorough detailing [max 100 words]. Example: the product started to rust after one year, although I was expecting it to last 5 years before rusting."
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
for id in reviews_df['id']:
    review = reviews_df[reviews_df['id'] == id]['review'].values[0]
    messages = [
        {"role": "user", "content": f"REVIEW: ```{review}```"},
    ]
    content_list.append(messages)

# Wrap your main coroutine invocation in another async function.
async def main():
    responses = await get_completion_list(content_list, max_parallel_calls, timeout, functions, function_call)
    return responses

# Now you can run your code using an await expression:
responses = await main()

# %%
reviews_df['initial_response'] = responses

# %%
initial_responses = responses.copy()

# %%
eval_responses = []
for item in initial_responses:
    data = item['function_call']['arguments']
    # Replace 'null' with 'None' in the data string before evaluation
    data = data.replace('null', 'None')
    eval_data = eval(data)
    eval_responses.append(eval_data)

reviews_df['eval_response'] = eval_responses

new_cols = list(reviews_df['eval_response'][3].keys())

# %%
new_cols

# %%
for col in new_cols:
    reviews_df[col] = np.nan

for i in reviews_df.index:
        for col in new_cols:
                try:
                    reviews_df[col][i] = reviews_df['eval_response'][i][col]
                except:
                     pass

# %%
reviews_df.columns

# %%
try:
    reviews_df.rename(columns = {'Issues?':'Issues'}, inplace = True)
except:
    pass

# %%
interim_reviews_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/reviews_df_interim.csv'
reviews_df.to_csv(interim_reviews_path, index=False)

# %%
reviews_df.columns


