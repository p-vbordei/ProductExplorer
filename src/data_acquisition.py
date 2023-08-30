###################### DATA ACQUISITION ######################
# data_acquisition.py
# %%

import time
import asyncio
import nest_asyncio
import aiohttp

try:
    from src.firebase_utils import initialize_firestore
except ImportError:
    try:
        from firebase_utils import initialize_firestore
    except ImportError:
        from .firebase_utils import initialize_firestore

# Your ASINs
asin_list = ['B09XM29XGF', 'B09WR4BW2Y']


# Amazon Scraper details
product_url = "https://amazonlive.p.rapidapi.com/product"
reviews_url = "https://amazonlive.p.rapidapi.com/reviews"
headers = {
    "X-RapidAPI-Key": "4da31a08e5mshaca05d98a3d9d6ep1fffb1jsn019717508cc8",
    "X-RapidAPI-Host": "amazonlive.p.rapidapi.com"
}

async def get_product_details(asin, retries=3):
    start = time.time()
    async with aiohttp.ClientSession() as session:
        params = {"asin": asin, "location": "us"}
        for _ in range(retries):
            async with session.get(product_url, headers=headers, params=params) as response:
                if response.status == 429:  # Rate limit hit
                    await asyncio.sleep(2)  # Wait for 2 seconds
                    continue
                elif response.status != 200:
                    print(f"Failed to fetch product details for {asin}. HTTP status: {response.status}")
                    return None
                print(f"Fetching product details for {asin} took {time.time() - start} seconds.")
                return await response.json()
        print(f"Failed to fetch product details for {asin} after {retries} retries.")
        return None

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
        async with session.get(reviews_url, headers=headers, params=params) as response:
            if response.status == 429:  # Rate limit hit
                await asyncio.sleep(2)  # Wait for 2 seconds
                continue
            elif response.status != 200:
                print(f"Failed to fetch reviews for {asin} page {page_var}. HTTP status: {response.status}")
                return None
            return await response.json()
    print(f"Failed to fetch reviews for {asin} page {page_var} after {retries} retries.")
    return None


async def get_product_reviews(asin):
    start = time.time()
    async with aiohttp.ClientSession() as session:
        # pages = ["1", "2", "3", "4", "5"]
        pages = ["1"]
        tasks = [fetch_reviews(session, page_var, asin) for page_var in pages]
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
            for review in review_page:  # Directly iterate over review_page
                review_id = review['id']
                review['asin'] = asin
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
# ######## TESTING FUNCTIONS #########


# Test function to get product details for the first ASIN
def test_get_product_details_for_first_asin():
    nest_asyncio.apply()
    asin = asin_list[0]
    details = asyncio.run(get_product_details(asin))
    print(f"Product details for ASIN {asin}:")
    print(details)
    return details

# Test function to get reviews for the first ASIN
def test_get_product_reviews_for_first_asin():
    nest_asyncio.apply()
    asin = asin_list[0]
    reviews = asyncio.run(get_product_reviews(asin))
    print(f"Reviews for ASIN {asin}:")
    for review_page in reviews:
        if review_page:
            for review in review_page:  # Directly iterate over review_page
                print(review)
    return reviews


# Test function to write product details and reviews for the first ASIN to Firebase
def test_write_to_firestore_for_first_asin():
    nest_asyncio.apply()
    asin = asin_list[0]
    db = initialize_firestore()
    
    # Fetch product details and reviews
    details = asyncio.run(get_product_details(asin))
    reviews = asyncio.run(get_product_reviews(asin))
    
    # Write to Firestore
    update_firestore(asin, details, reviews, db)
# %%
###### TESTS #########

# %%

# Product Details
#print("\nFetching product details for the first ASIN...")
#test_get_product_details_for_first_asin()

# %%
# Reviews
#print("\nFetching reviews for the first ASIN...")
#test_get_product_reviews_for_first_asin()
# %%
# Firestore
#print("\nWriting product details and reviews for the first ASIN to Firebase...")
#test_write_to_firestore_for_first_asin()


# %%
# ====================