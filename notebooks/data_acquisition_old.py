###################### DATA ACQUISITION ######################
# data_acquisition.py
# https://rapidapi.com/eaidoo015-pj8dZiAnLJJ/api/youtube-scraper-2023/pricing
# https://rapidapi.com/felixeschmittfes/api/amazonlive/pricing
# %%
import time
import asyncio
import aiohttp
import nest_asyncio
import logging 
logging.basicConfig(level=logging.INFO)

# Importing Firestore initialize function
try:
    from src.firebase_utils import initialize_firestore
except (ImportError, ModuleNotFoundError):
    from firebase_utils import initialize_firestore

# API details
product_url = "https://amazonlive.p.rapidapi.com/product"
reviews_url = "https://amazonlive.p.rapidapi.com/reviews"
headers = {
    "X-RapidAPI-Key": "YOUR_API_KEY",
    "X-RapidAPI-Host": "amazonlive.p.rapidapi.com"
}

# API rate settings
api_rate = 1  
sleep_time = 1 / api_rate  


from google.cloud import pubsub_v1

def initialize_pubsub():
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path('your_project_id', 'your_topic_name')
    return publisher, topic_path


async def fetch_reviews(session, page_var, asin, retries=3):
    params = {
        "asin": asin,
        "location": "us",
        "page": page_var,
        "amount": "20",
        "sort_by_recent": "false",
        "only_verified": "true"
    }
    for _ in range(retries):
        try:
            async with session.get(reviews_url, headers=headers, params=params) as response:
                if response.status == 429:
                    logging.warning(f"Rate limit hit for {asin} page {page_var}. Sleeping.")
                    await asyncio.sleep(sleep_time)
                    continue
                elif response.status != 200:
                    logging.error(f"Failed for {asin} page {page_var}. HTTP: {response.status}")
                    return None
                return await response.json()
        except Exception as e:
            logging.exception(f"Error fetching reviews for {asin} page {page_var}: {e}")
            return None
    logging.error(f"Failed for {asin} page {page_var} after {retries} retries.")
    return None



async def get_product_reviews(asin):
    start = time.time()
    async with aiohttp.ClientSession() as session:
        pages = ["1", "2"]
        tasks = [fetch_reviews(session, page_var, asin) for page_var in pages]
        results = await asyncio.gather(*tasks)
        print(f"Fetched for {asin} in {time.time() - start} seconds.")
        return results

def update_firestore_reviews(asin, reviews, db):
    if reviews is None or any(r is None for r in reviews):
        print(f"Skipping Firestore for {asin}. Missing data.")
        return
    start = time.time()
    doc_ref = db.collection('products').document(asin)
    batch = db.batch()
    for review_page in reviews:
        for review in review_page.get('reviews', []):
            review_id = review['id']
            review_ref = doc_ref.collection('reviews').document(review_id)
            batch.set(review_ref, review)
    batch.commit()
    print(f"Updated Firestore for {asin} in {time.time() - start} seconds.")

async def process_asin(asin, db):
    try:
        await asyncio.sleep(sleep_time)
        reviews = await get_product_reviews(asin)
        update_firestore_reviews(asin, reviews, db)
    except Exception as e:
        logging.exception(f"Error processing ASIN {asin}: {e}")

async def run_data_acquisition(asinList):
    try:
        db = initialize_firestore()
        tasks = [process_asin(asin, db) for asin in asinList]
        await asyncio.gather(*tasks)
        logging.info("Data acquisition complete.")
        return True
    except Exception as e:
        logging.exception(f"Error in run_data_acquisition: {e}")
        return False

def execute_data_acquisition(asinList):
    try:
        nest_asyncio.apply()
        return asyncio.run(run_data_acquisition(asinList))
    except Exception as e:
        logging.exception(f"Error in execute_data_acquisition: {e}")
        return False
# =========================