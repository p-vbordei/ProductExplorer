######################
# data_acquisition.py
# %%

import time
import asyncio
import nest_asyncio
import aiohttp

try:
    from src.firebase_utils import initialize_firestore
except ImportError:
    from firebase_utils import initialize_firestore

# Your ASINs
asin_list = ['B08X2324ZL', 'B09MQ689XL']

# Amazon Scraper details
base_url = "https://asin-data.p.rapidapi.com/request"
api_key = "70201ee0c8ed29661bc6ae00a84341fb"
headers = {
	"X-RapidAPI-Key": "4da31a08e5mshaca05d98a3d9d6ep1fffb1jsn019717508cc8",
	"X-RapidAPI-Host": "asin-data.p.rapidapi.com"
}


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

def update_firestore(asin, details, reviews, db):
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

async def process_asin(asin, db):
    details = await get_product_details(asin)
    if details is None:
        print(f"Skipping {asin} due to failed details fetch.")
        return
    reviews = await get_product_reviews(asin)
    if reviews is None or any(review is None for review in reviews):
        print(f"Skipping {asin} due to failed reviews fetch.")
        return
    update_firestore(asin, details, reviews, db)


async def run_data_acquisition(asin_list):
    try:
        db = initialize_firestore()
        tasks = [process_asin(asin, db) for asin in asin_list]
        await asyncio.gather(*tasks)
        return True
    except Exception as e:
        print(f"Error during data acquisition: {e}")
        return False

def execute_data_acquisition(asin_list):
    nest_asyncio.apply()
    return asyncio.run(run_data_acquisition(asin_list))
# %%
# ====================