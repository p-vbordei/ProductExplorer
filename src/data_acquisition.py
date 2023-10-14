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
import json
from google.cloud import pubsub_v1
logging.basicConfig(level=logging.INFO)

try:
    from src.firebase_utils import initialize_firestore, initialize_gae
except (ImportError, ModuleNotFoundError):
    from firebase_utils import initialize_firestore, initialize_gae

if not FIREBASE_KEY:
    from dotenv import load_dotenv
    load_dotenv()
    FIREBASE_KEY = os.getenv('FIREBASE_KEY')


headers = {
    "X-RapidAPI-Key": "YOUR_API_KEY",
    "X-RapidAPI-Host": "amazonlive.p.rapidapi.com"
}
reviews_url = "https://amazonlive.p.rapidapi.com/reviews"
api_rate = 1
sleep_time = 1 / api_rate


project_id = "productexplorerdata"
topic_id = "asin-data-acquisition"
subscription_id = "asin-data-subscription"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)


def publish_to_pubsub(asin):
    data = json.dumps({"asin": asin})
    data = data.encode("utf-8")
    future = publisher.publish(topic_path, data)
    print(f"Published message for {asin}")


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
        publish_to_pubsub(asin)
    except Exception as e:
        logging.exception(f"Error processing ASIN {asin}: {e}")


async def fetch_data_for_asin(message):
    asin_data = json.loads(message.data.decode("utf-8"))
    asin = asin_data.get("asin", None)
    if asin:
        db = initialize_firestore()
        reviews = await get_product_reviews(asin)
        update_firestore_reviews(asin, reviews, db)


def callback(message):
    asyncio.run(fetch_data_for_asin(message))
    message.ack()


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
        # Initialize the event loop
        nest_asyncio.apply()
        
        # Run the data acquisition tasks for the given ASINs
        acquisition_status = asyncio.run(run_data_acquisition(asinList))
        
        if not acquisition_status:
            logging.error("Data acquisition failed.")
            return False

        # Set up the Pub/Sub subscription and start listening for messages
        print(f"Listening for messages on {subscription_path}..\n")
        
        try:
            streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            streaming_pull_future.result()
        except Exception as e:
            logging.exception(f"Error setting up subscription: {e}")
            return False
        
        return True

    except Exception as e:
        logging.exception(f"Error in execute_data_acquisition: {e}")
        return False

# %%
# =========================