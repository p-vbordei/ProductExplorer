# %%
import numpy as np
import pandas as pd
import tiktoken

from openai.embeddings_utils import get_embedding
from sklearn.cluster import AgglomerativeClustering

#https://github.com/itayzit/openai-async
import openai_async


import os
import openai
from dotenv import load_dotenv
# from sqlalchemy import create_engine

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if os.getenv("OPENAI_API_KEY") is not None:
    print ("OPENAI_API_KEY is ready")
else:
    print ("OPENAI_API_KEY environment variable not found")

import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt

GPT_MODEL = "gpt-3.5-turbo"


# %% [markdown]
# # Obiectiv Fisier
# - identific topics, apoi clusterizez si denumesc din nou, daca e nevoie
# - identific atribute asociate cu topics, apoi le clusterizez si denumesc din nou
# - fiecare topic si atribut trebuie sa aibe asociate rating-ul, ID-ul review-ului si asin-ul, sentimentele asociate.
# - plec la drum cu un fisier de reivews redus la minimul necesar. Acelasi fisier de reviews data va fi extins (exploded) astfel incat atributele sa fie specifice unei baze de date:
# 
# "Attribute" (exemplu: when)
# si value

# %%
interim_reviews_path = interim_reviews_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/reviews_df_interim.csv'
reviews = pd.read_csv(interim_reviews_path)

# %%
reviews

# %%
reviews.drop(columns = [ 'Verified', 'Helpful', 'Title', 'review','Videos','Variation', 'Style', 'num_tokens', 'review_num_tokens', 'eval_response'], inplace = True)

# %%
data_cols = ["Review Summary","Buyer Motivation", "Customer Expectations", "How the product is used", "Where the product is used", "User Description", "Packaging", "Season", "When the product is used", "Price", "Quality", "Durability", "Ease of Use", "Setup and Instructions", "Noise and Smell", "Colors", "Size and Fit", "Danger Appraisal", "Design and Appearance", "Parts and Components", "Issues"]
for col in data_cols:
    reviews[col] = reviews[col].fillna('')
    reviews[col].replace(['\n', 'not mentioned',np.nan, '',' ', 'NA', 'N/A', 'missing', 'NaN', 'unknown', 'Not mentioned','not specified','Not specified'], 'unknown', inplace = True)

# %%
columns_to_pivot = ["Buyer Motivation", "Customer Expectations", "How the product is used", "Where the product is used", "User Description", "Packaging", "Season", "When the product is used", "Price", "Quality", "Durability", "Ease of Use", "Setup and Instructions", "Noise and Smell", "Colors", "Size and Fit", "Danger Appraisal", "Design and Appearance", "Parts and Components", "Issues"]

# assume 'df' is your DataFrame
reviews_data_df = reviews.melt(id_vars=[col for col in reviews.columns if col not in columns_to_pivot], 
                    value_vars=columns_to_pivot, 
                    var_name='Attribute', 
                    value_name='Value')

# %%
reviews_data_df = reviews_data_df[reviews_data_df['Value'] != 'unknown']

# %% [markdown]
# # Clustering

# %%
df = reviews_data_df

# %%
# omit reviews that are too long to embed
df["n_tokens"] = df['Value'].apply(lambda x: len(encoding.encode(x)))
df = df[df.n_tokens <= max_tokens]

# %%
# Get Embeddings in Async mode

import numpy as np
import asyncio
import aiohttp
import pandas as pd
import random
import nest_asyncio
from typing import List

# This will allow nested running of event loops in Jupyter
nest_asyncio.apply()

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

# Use asyncio's run method to start the event loop and run process_dataframe
df = asyncio.run(process_dataframe(df))

df["embedding"] = df["embedding"].apply(np.array)  # convert string to numpy array

# %%
max_n_clusters = 7
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

# %%
cluster_df  = df[['Attribute', 'cluster','Value']].drop_duplicates()

# %%
cluster_df.drop_duplicates()
cluster_df

# %% [markdown]
# # Get label for the clusters

# %%
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
eval_responses = []
for item in responses:
    data = item['function_call']['arguments']
    eval_data = eval(data)
    eval_responses.append(eval_data['cluster_label'])

# %%
cluster_response_df= cluster_df.drop(columns = ['Value']).drop_duplicates()
cluster_response_df['cluster_label'] = eval_responses

# %%
df_with_clusters = df.merge(cluster_response_df, on = ['Attribute', 'cluster'], how = 'left')
df_with_clusters.drop(columns = ['n_tokens', 'embedding','Date', 'Author','Images'], inplace = True)

# %%
interim_reviews_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/reviews_df_interim.csv'
reviews = pd.read_csv(interim_reviews_path)

# %%
df_with_clusters.columns

# %%
reviews_with_clusters = df_with_clusters.merge(reviews[['URL', 'Date', 'Author','Verified', 'Helpful', 'Title', 'review',  'Images', 'Videos','Variation', 'Style' ]], on = ['URL'], how = 'left')

# %%
reviews_with_clusters_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/reviews_with_clusters.csv'
reviews_with_clusters.to_csv(reviews_with_clusters_path)

# %% [markdown]
# # Quantify observations

# %%
df_with_clusters['positive_sentiment'] = df_with_clusters['positive_sentiment'].astype(float)
df_with_clusters['negative_sentiment'] = df_with_clusters['negative_sentiment'].astype(float)


agg_result = df_with_clusters.groupby(['Attribute', 'cluster_label']).agg({
    'positive_sentiment': 'mean', 
    'negative_sentiment': 'mean',
    'Rating': lambda x: list(x),
    'id': lambda x: list(x),
    'asin': lambda x: list(x),
    'URL': lambda x: list(x),
    }).reset_index()

# Aggregate the count separately
count_result = df_with_clusters.groupby(['Attribute', 'cluster_label']).size().reset_index(name='observation_count')
attribute_clusters_with_percentage = pd.merge(agg_result, count_result, on=['Attribute', 'cluster_label'])


# Calculate the average rating
m = []
for e in attribute_clusters_with_percentage['Rating']:
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


total_observations_per_attribute = df_with_clusters.groupby('Attribute').size()

attribute_clusters_with_percentage = attribute_clusters_with_percentage.set_index('Attribute')  # set 'Attribute' as the index to allow for division
attribute_clusters_with_percentage['percentage_of_observations_vs_total_number_per_attribute'] = attribute_clusters_with_percentage['observation_count'] / total_observations_per_attribute * 100
attribute_clusters_with_percentage = attribute_clusters_with_percentage.reset_index()  # reset the index if desired

number_of_reviews = reviews_with_clusters['URL'].unique().shape[0]
number_of_reviews
attribute_clusters_with_percentage['percentage_of_observations_vs_total_number_of_reviews'] = attribute_clusters_with_percentage['observation_count'] / number_of_reviews * 100


# %%
attribute_clusters_with_percentage.head(3)

# %%
attribute_clusters_with_percentage_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/attribute_clusters_with_percentage.csv'
attribute_clusters_with_percentage.to_csv(attribute_clusters_with_percentage_path, index = False)

# %%
df_with_clusters['positive_sentiment'] = df_with_clusters['positive_sentiment'].astype(float)
df_with_clusters['negative_sentiment'] = df_with_clusters['negative_sentiment'].astype(float)

agg_result = df_with_clusters.groupby(['Attribute', 'cluster_label', 'asin']).agg({
    'positive_sentiment': 'mean', 
    'negative_sentiment': 'mean',
    'Rating': lambda x: list(x),
    'id': lambda x: list(x),
    'URL': lambda x: list(x),
}).reset_index()

# Aggregate the count separately
count_result = df_with_clusters.groupby(['Attribute', 'cluster_label', 'asin']).size().reset_index(name='observation_count')
attribute_clusters_with_percentage_by_asin = pd.merge(agg_result, count_result, on=['Attribute', 'cluster_label', 'asin'])

# Calculate the average rating
m = []
for e in attribute_clusters_with_percentage_by_asin['Rating']:
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

# Compute the total observations per attribute and asin
df_with_clusters['total_observations_per_attribute_asin'] = df_with_clusters.groupby(['Attribute', 'asin'])['asin'].transform('count')

# Calculate the percentage
attribute_clusters_with_percentage_by_asin['percentage_of_observations_vs_total_number_per_attribute'] = attribute_clusters_with_percentage_by_asin['observation_count'] / df_with_clusters['total_observations_per_attribute_asin'] * 100

number_of_reviews = reviews_with_clusters['URL'].unique().shape[0]
attribute_clusters_with_percentage_by_asin['percentage_of_observations_vs_total_number_of_reviews'] = attribute_clusters_with_percentage_by_asin['observation_count'] / number_of_reviews * 100


# %%
attribute_clusters_with_percentage_by_asin.head(3)

# %%
attribute_clusters_with_percentage_by_asin_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/attribute_clusters_with_percentage_by_asin.csv'
attribute_clusters_with_percentage_by_asin.to_csv(attribute_clusters_with_percentage_by_asin_path, index = False)


