###################### DATA ACQUISITION ######################
# data_acquisition.py
# https://rapidapi.com/eaidoo015-pj8dZiAnLJJ/api/youtube-scraper-2023/pricing
# https://rapidapi.com/felixeschmittfes/api/amazonlive/pricing
# %%
import time
import asyncio
import aiohttp
import nest_asyncio

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

# Variable to hold API rate (requests per second)
api_rate = 1  # Change this to 5 or 100 as needed ( requests per second)

async def fetch_reviews(session, page_var, asin, retries=3):
    params = {
        "asin": asin,
        "location": "us",
        "page": page_var,
        "amount": "20",
        "sort_by_recent": "false",
        "only_verified": "true"
    }
    sleep_time = 1 / api_rate  # Calculate sleep time based on rate
    for _ in range(retries):
        async with session.get(reviews_url, headers=headers, params=params) as response:
            if response.status == 429:
                await asyncio.sleep(sleep_time)  # Sleep based on API rate
                continue
            elif response.status != 200:
                print(f"Failed for {asin} page {page_var}. HTTP: {response.status}")
                return None
            return await response.json()
    print(f"Failed for {asin} page {page_var} after {retries} retries.")
    return None

# (The rest of your code remains unchanged)


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
    reviews = await get_product_reviews(asin)
    update_firestore_reviews(asin, reviews, db)

async def run_data_acquisition(asinList):
    try:
        db = initialize_firestore()
        tasks = [process_asin(asin, db) for asin in asinList]
        await asyncio.gather(*tasks)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def execute_data_acquisition(asinList):
    nest_asyncio.apply()
    return asyncio.run(run_data_acquisition(asinList))
# =========================