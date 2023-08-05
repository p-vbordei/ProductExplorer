
# %%
import aiofiles
import os
import json
from tqdm import tqdm

import time
import asyncio
import nest_asyncio
import aiohttp
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import concurrent.futures

# Firestore details
cred_path = '/Users/vladbordei/Documents/Development/ProductExplorer/notebooks/productexplorerdata-firebase-adminsdk-ulb3d-465f23dff3.json'

# Initialize Firestore
cred = credentials.Certificate(cred_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# %%
prod_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/external/product_jsons'

#%%
async def upload_to_firestore(filename):
    try:
        f = await aiofiles.open(os.path.join(prod_path, filename), 'r')
        data = await f.read()
        data = json.loads(data)
        data = data[0]
        asin = data['asin']
        doc_ref = db.collection('products').document(asin)
        doc_ref.set({
            'details': data,
        }, merge=True)
    finally:
        await f.close()

#%%

async def upload_product_jsons():
    files = os.listdir(prod_path)
    tasks = [upload_to_firestore(filename) for filename in tqdm(files)]
    await asyncio.gather(*tasks)

#%%
nest_asyncio.apply()
# to run the function
loop = asyncio.get_event_loop()
loop.run_until_complete(upload_product_jsons())


# %%
rev_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/external/review_jsons'
db = firestore.client()  # assuming db is defined earlier as your Firestore client

async def upload_reviews_to_firestore(filename):
    try:
        f = await aiofiles.open(os.path.join(rev_path, filename), 'r')
        data = await f.read()
        data = json.loads(data)
        asin = data[0]['asin']['original']
        doc_ref = db.collection('products').document(asin)
        doc_ref.set({
            'reviews': data,
        }, merge=True)
    finally:
        await f.close()

async def upload_review_jsons():
    files = os.listdir(rev_path)
    tasks = [upload_reviews_to_firestore(filename) for filename in tqdm(files)]
    await asyncio.gather(*tasks)

nest_asyncio.apply()
# to run the function
loop = asyncio.get_event_loop()
loop.run_until_complete(upload_review_jsons())


# %%
