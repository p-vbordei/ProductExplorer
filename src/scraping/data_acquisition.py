# %%
import requests
import json
import pandas as pd

# %%
asin_list_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/external/asin_list.csv'
asin_list = pd.read_csv(asin_list_path)['asin'].tolist()


# %%

import time
import asyncio
import nest_asyncio
import aiohttp
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore



# Your ASINs
asin_list = ['B08X2324ZL', 'B09MQ689XL']

# Amazon Scraper details
base_url = "https://asin-data.p.rapidapi.com/request"
api_key = "70201ee0c8ed29661bc6ae00a84341fb"
headers = {
	"X-RapidAPI-Key": "4da31a08e5mshaca05d98a3d9d6ep1fffb1jsn019717508cc8",
	"X-RapidAPI-Host": "asin-data.p.rapidapi.com"
}

# Firestore details
cred_path = '/Users/vladbordei/Documents/Development/ProductExplorer/notebooks/productexplorerdata-firebase-adminsdk-ulb3d-465f23dff3.json'

# Initialize Firestore
cred = credentials.Certificate(cred_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

async def get_product_details(asin):
    start = time.time()
    async with aiohttp.ClientSession() as session:
        url = f"{base_url}{asin}"
        async with session.get(url, headers=headers, params={"api_key": api_key}) as response:
            if response.status != 200:
                print(f"Failed to fetch product details for {asin}. HTTP status: {response.status}")
                return None
            print(f"Fetching product details for {asin} took {time.time() - start} seconds.")
            return await response.json()

async def fetch(session, page_var, asin):
    params = {
        "type":"reviews",
        "asin":asin,
        "amazon_domain":"amazon.com",
        "reviewer_type":"verified_purchase",
        "sort_by":"most_recent",
        "global_reviews":"false",
        "page":page_var
    }
    async with session.get(url=base_url, headers=headers, params=params) as response:
        if response.status != 200:
            print(f"Failed to fetch reviews for {asin} page {page_var}. HTTP status: {response.status}")
            return None
        return await response.json()

async def get_product_reviews(asin):
    start = time.time()
    async with aiohttp.ClientSession() as session:
        pages = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        tasks = [fetch(session, page_var, asin) for page_var in pages]
        results = await asyncio.gather(*tasks)
        print(f"Fetching product reviews for {asin} took {time.time() - start} seconds.")
        return results

def update_firestore(asin, details, reviews):
    if details is None or reviews is None or any(review is None for review in reviews):
        print(f"Skipping Firestore update for {asin} due to missing data.")
        return
    start = time.time()
    doc_ref = db.collection('products').document(asin)
    doc_ref.set({
        'details': details,
        'reviews': reviews
    }, merge=True)
    print(f"Updating Firestore for {asin} took {time.time() - start} seconds.")

async def process_asin(asin):
    details = await get_product_details(asin)
    if details is None:
        print(f"Skipping {asin} due to failed details fetch.")
        return
    reviews = await get_product_reviews(asin)
    if reviews is None or any(review is None for review in reviews):
        print(f"Skipping {asin} due to failed reviews fetch.")
        return
    update_firestore(asin, details, reviews)

async def main():
    tasks = [process_asin(asin) for asin in asin_list]
    await asyncio.gather(*tasks)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())



# /Users/vladbordei/Documents/Development/ProductExplorer/data/external/asins


############

##### UPDATED MODEL, NOT TESTED
#### BATCH WRITING AND NEW DATA STRUCTURE


import time
import asyncio
import nest_asyncio
import aiohttp
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


# Your ASINs
asin_list = ['B08X2324ZL', 'B09MQ689XL']

# Amazon Scraper details
base_url = "https://asin-data.p.rapidapi.com/request"
api_key = "70201ee0c8ed29661bc6ae00a84341fb"
headers = {
	"X-RapidAPI-Key": "4da31a08e5mshaca05d98a3d9d6ep1fffb1jsn019717508cc8",
	"X-RapidAPI-Host": "asin-data.p.rapidapi.com"
}

# Firestore details
cred_path = '/Users/vladbordei/Documents/Development/ProductExplorer/notebooks/productexplorerdata-firebase-adminsdk-ulb3d-465f23dff3.json'

# Initialize Firestore
cred = credentials.Certificate(cred_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

async def get_product_details(asin):
    start = time.time()
    async with aiohttp.ClientSession() as session:
        url = f"{base_url}{asin}"
        async with session.get(url, headers=headers, params={"api_key": api_key}) as response:
            if response.status != 200:
                print(f"Failed to fetch product details for {asin}. HTTP status: {response.status}")
                return None
            print(f"Fetching product details for {asin} took {time.time() - start} seconds.")
            return await response.json()

async def fetch(session, page_var, asin):
    params = {
        "type":"reviews",
        "asin":asin,
        "amazon_domain":"amazon.com",
        "reviewer_type":"verified_purchase",
        "sort_by":"most_recent",
        "global_reviews":"false",
        "page":page_var
    }
    async with session.get(url=base_url, headers=headers, params=params) as response:
        if response.status != 200:
            print(f"Failed to fetch reviews for {asin} page {page_var}. HTTP status: {response.status}")
            return None
        return await response.json()

async def get_product_reviews(asin):
    start = time.time()
    async with aiohttp.ClientSession() as session:
        pages = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        tasks = [fetch(session, page_var, asin) for page_var in pages]
        results = await asyncio.gather(*tasks)
        print(f"Fetching product reviews for {asin} took {time.time() - start} seconds.")
        return results

def update_firestore(asin, details, reviews):
    if details is None or reviews is None or any(review is None for review in reviews):
        print(f"Skipping Firestore update for {asin} due to missing data.")
        return
    start = time.time()
    doc_ref = db.collection('products').document(asin)
    
    # Set details field in the document
    doc_ref.set({
        'details': details
    }, merge=True)

    # Initialize Firestore batch
    batch = db.batch()
    for review_page in reviews:
        if review_page is not None:
            for review in review_page['reviews']:
                review_id = review['id']
                review_ref = doc_ref.collection('reviews').document(review_id)
                batch.set(review_ref, review)

    # Commit the batch
    batch.commit()

    print(f"Updating Firestore for {asin} took {time.time() - start} seconds.")

async def process_asin(asin):
    details = await get_product_details(asin)
    if details is None:
        print(f"Skipping {asin} due to failed details fetch.")
        return
    reviews = await get_product_reviews(asin)
    if reviews is None or any(review is None for review in reviews):
        print(f"Skipping {asin} due to failed reviews fetch.")
        return
    update_firestore(asin, details, reviews)

async def main():
    tasks = [process_asin(asin) for asin in asin_list]
    await asyncio.gather(*tasks)

nest_asyncio.apply()

# to run the function
loop = asyncio.get_event_loop()
loop.run_until_complete(main())

# %%
