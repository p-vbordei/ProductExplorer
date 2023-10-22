###################### DATA ACQUISITION ######################
# data_acquisition.py
# %%
import asyncio
import aiohttp
import logging
import json
from google.cloud import pubsub_v1

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Import custom modules
try:
    from src.firebase_utils import initialize_firestore, initialize_gae, initialize_pub_sub
except (ImportError, ModuleNotFoundError):
    from firebase_utils import initialize_firestore, initialize_gae, initialize_pub_sub

def initialize_rapid_api():
    """Initialize configurations"""
    global headers, reviews_url, api_rate, sleep_time
    
    # API Configuration
    headers = {"X-RapidAPI-Key": "YOUR_API_KEY", "X-RapidAPI-Host": "amazonlive.p.rapidapi.com"}
    reviews_url = "https://amazonlive.p.rapidapi.com/reviews"
    api_rate = 1
    sleep_time = 1 / api_rate

async def publish_to_pubsub(asin):
    """Publish ASIN to Pub/Sub asynchronously."""
    data = json.dumps({"asin": asin}).encode("utf-8")
    await loop.run_in_executor(None, publisher.publish, topic_path, data)
    logging.info(f"Published message for {asin}")

async def process_asin(asin):
    """Process an individual ASIN."""
    try:
        # Fetch product reviews
        reviews = await get_product_reviews(asin)
        
        # Update Firestore with the reviews
        await update_firestore_reviews(asin, reviews)
        
        logging.info(f"Successfully processed {asin}")
        
    except Exception as e:
        logging.error(f"Failed to process {asin}: {e}")


async def fetch_reviews(session, page_var, asin, retries=3):
    """Fetch product reviews asynchronously."""
    # Initialize Google App Engine
    initialize_gae()

    params = {
        "asin": asin,
        "location": "us",
        "page": page_var,
        "amount": "20",
        "sort_by_recent": "false",
        "only_verified": "true"
    }
    for retry in range(retries):
        try:
            async with session.get(reviews_url, headers=headers, params=params) as response:
                if response.status == 429:
                    logging.warning(f"Rate limit reached for {asin} page {page_var}. Retrying.")
                    await asyncio.sleep(sleep_time)
                    continue
                elif response.status == 200:
                    return await response.json()
                else:
                    logging.error(f"Failed to fetch for {asin} page {page_var}. HTTP status: {response.status}")
                    return None
        except Exception as e:
            logging.error(f"Fetch failed for {asin} page {page_var}. Error: {e}")
            return None

    logging.error(f"Fetch failed for {asin} page {page_var} after {retries} retries.")
    return None

async def get_product_reviews(asin):
    """Get product reviews for a given ASIN."""
    async with aiohttp.ClientSession() as session:
        # Create tasks for each page you want to scrape
        pages = ["1", "2"]
        tasks = [fetch_reviews(session, page, asin) for page in pages]
        return await asyncio.gather(*tasks)

async def update_firestore_reviews(asin, reviews):
    """Update Firestore with fetched reviews asynchronously."""
    if not all(reviews):
        logging.warning(f"Skipping Firestore update for {asin} due to missing data.")
        return
    batch = db.batch()
    doc_ref = db.collection('products').document(asin)
    for review_page in reviews:
        for review in review_page.get('reviews', []):
            review_ref = doc_ref.collection('reviews').document(review['id'])
            batch.set(review_ref, review)
    batch.commit()
    logging.info(f"Firestore updated for {asin}")

async def fetch_data_for_asin(message):
    """Fetch data for an ASIN based on a Pub/Sub message."""
    asin_data = json.loads(message.data.decode("utf-8"))
    asin = asin_data.get("asin")
    if asin:
        reviews = await get_product_reviews(asin)
        await update_firestore_reviews(asin, reviews)
    message.ack()

async def callback(message):
    """Callback function for Pub/Sub subscription."""
    await fetch_data_for_asin(message)

async def run_data_acquisition(asin_list):
    # Check if asin_list is a single ASIN string and not a list
    if isinstance(asin_list, str) and len(asin_list) == 10 and asin_list.startswith("B"):
        asin_list = [asin_list]

    try:
        tasks = [process_asin(asin) for asin in asin_list]
        await asyncio.gather(*tasks)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def execute_data_acquisition(asin_list):
    """Execute data acquisition process."""
    
    initialize_pub_sub()
    initialize_rapid_api()
    initialize_firestore()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # If loop is running, use create_task to schedule the coroutine
        loop.create_task(run_data_acquisition(asin_list))
    else:
        # If loop is not running, start it up and run the coroutine
        loop.run_until_complete(run_data_acquisition(asin_list))

    logging.info(f"Listening for messages on {subscription_path}")

    try:
        # Start or attach the pub/sub subscription
        if not loop.is_running():
            streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
            loop.run_until_complete(streaming_pull_future)
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
        logging.info("Subscription cancelled.")
    except Exception as e:
        logging.error(f"Failed to set up subscription: {e}")


# =============================================================================

# %%

asin_list = ["B088YHHS8D"]