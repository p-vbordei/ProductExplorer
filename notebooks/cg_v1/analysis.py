# analysis.py

import pandas as pd
import numpy as np
import asyncio
import nest_asyncio
import openai
from sklearn.cluster import AgglomerativeClustering
import aiohttp
import random

# Constants
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_ENCODING = "cl100k_base"
MAX_TOKENS = 8000

async def generate_embedding(text, model=EMBEDDING_MODEL, api_key=None):
    """Generate embeddings for a given text."""
    async with aiohttp.ClientSession() as session:
        for attempt in range(6):
            try:
                async with session.post(
                    "https://api.openai.com/v1/embeddings",
                    json={"input": [text], "model": model},
                    headers={"Authorization": f"Bearer {api_key or openai.api_key}"},
                ) as response:
                    data = await response.json()
                    return np.array(data["data"][0]["embedding"])
            except Exception as e:
                wait_time = random.uniform(1, min(20, 2 ** attempt))
                print(f"Request failed with {e}, retrying in {wait_time} seconds.")
                await asyncio.sleep(wait_time)
        print("Failed to get embedding after 6 attempts, returning None.")
        return None

        
def vectorize_reviews(cleaned_reviews):
    """Generate embeddings for each review"""

    loop = asyncio.get_event_loop()
    embeddings = loop.run_until_complete(
        asyncio.gather(*[generate_embedding(text) for text in cleaned_reviews["clean_review_text"]])
    )

    cleaned_reviews["embedding"] = list(embeddings)

    return cleaned_reviews


def cluster_reviews(vectorized_reviews):
    """Cluster reviews using hierarchical clustering"""

    # Determine optimal number of clusters
    num_clusters = 5

    clustering = AgglomerativeClustering(n_clusters=num_clusters)
    clustering.fit(vectorized_reviews["embedding"].tolist())

    vectorized_reviews["cluster"] = clustering.labels_

    return vectorized_reviews


def analyze_clusters(clustered_reviews):
    """Use GPT-3 to analyze clusters and identify topics"""

    cluster_topics = {}

    for cluster_id in clustered_reviews["cluster"].unique():
        subset = clustered_reviews[clustered_reviews["cluster"] == cluster_id]

        samples = subset["clean_review_text"].sample(5).tolist()

        prompt = f"Read these sample reviews and summarize the common topic: {samples}"

        response = openai.Completion.create(
            engine="text-davinci-002", 
            prompt=prompt,
            max_tokens=60
        )

        topic = response["choices"][0]["text"].strip()
        cluster_topics[cluster_id] = topic

    return cluster_topics


def label_clusters(clustered_reviews, cluster_topics):
    
    cluster_df = clustered_reviews[["cluster", "clean_review_text"]]
    
    content_list = []

    for cluster_id, topic in cluster_topics.items():
        subset = cluster_df[cluster_df["cluster"] == cluster_id]
        values = subset["clean_review_text"].tolist()[:5]
        
        prompt = f"Topic: {topic}. Values: {values}. Generate a 7 word label summarizing this topic."
        
        content_list.append({"prompt": prompt, "model": "text-davinci-002"})

    responses = openai.BatchCompletion.create(content_list)
    
    labels = [r.choices[0].text.strip() for r in responses]
    
    clustered_reviews["cluster_label"] = labels

    return clustered_reviews


def extract_issues(labeled_clusters):
    """Extract key issues from labeled clusters"""

    issues = {}

    for cluster_id, label in labeled_clusters["cluster_label"].items():
        if is_issue(label):
            issue = infer_issue(label)
            subset = labeled_clusters[labeled_clusters["cluster"] == cluster_id]
            
            # Extract example quotes
            issues[issue] = []

    return issues