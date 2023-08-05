# %% [markdown]
# ## STRUCTURE
# - Read Scraped Reviews & Products
#     - Create the asin list
#     - Create reviews lists, parse by ASIN
#     - Create products lists, parse by ASIN
# - Save results
# 
# 

# %%
import pandas as pd

from dotenv import load_dotenv
import os

load_dotenv()
# %%
# asin_list_path = './data/external/asin_list.csv'
asin_list_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/external/asin_list.csv'
asin_list = pd.read_csv(asin_list_path)['asin'].tolist()

# %%
def read_data(folder_path):
    reviews = pd.DataFrame()
    
    for file_name in os.listdir(folder_path):
        if file_name.startswith("reviews"):
            file_path = os.path.join(folder_path, file_name)
            df = pd.read_csv(file_path)
            reviews = pd.concat([reviews, df])
    return reviews



# %%
def read_data_from_filtered_h10_folder(folder_path):
    reviews = pd.DataFrame()
    
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        df = pd.read_csv(file_path)
        reviews = pd.concat([reviews, df])
    
    return reviews


# %%
reviews_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/raw/RaisedGardenBed/h10reviews'
# reviews = read_data(reviews_path)
reviews = read_data_from_filtered_h10_folder(reviews_path)

# %%
try:
    reviews.rename(columns={'Body': 'review'}, inplace=True)
except:
    pass


# %%
# save_path = './data/interim/reviews.csv'
save_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/reviews.csv'
reviews.to_csv(save_path, index=False)

# %%
# https://firebase.google.com/docs/firestore/quickstart?authuser=0&_gl=1*2w73qq*_ga*OTM3NzQyMjU5LjE2OTAzMDU0MTU.*_ga_CW55HF8NVT*MTY5MDQ2MDMyNC4yLjEuMTY5MDQ2MTA3MC4wLjAuMA..#python
# https://www.youtube.com/watch?v=b4W3YQdViTI
# https://www.youtube.com/watch?v=N0j6Fe2vAK4

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account.
cred = credentials.Certificate('/Users/vladbordei/Documents/Development/ProductExplorer/notebooks/productexplorerdata-firebase-adminsdk-ulb3d-465f23dff3.json')

app = firebase_admin.initialize_app(cred)

db = firestore.client()
# %%




import time
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Your ASINs
asin_list = ['B08X2324ZL', 'B09MQ689XL']

# Firestore details
cred_path = '/Users/vladbordei/Documents/Development/ProductExplorer/notebooks/productexplorerdata-firebase-adminsdk-ulb3d-465f23dff3.json'

# Initialize Firestore
cred = credentials.Certificate(cred_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Loading details from CSV
def load_details_from_csv(asin):
    # Assuming your dataframe is named df and the ASIN column is named 'asin'
    df = pd.read_csv('details.csv')
    details = df[df['asin'] == asin].to_dict('records')[0] # We assume that there is only one detail row per ASIN
    return details

# Loading reviews from CSV
def load_reviews_from_csv(asin):
    # Assuming your dataframe is named df and the ASIN column is named 'asin'
    df = pd.read_csv('reviews.csv')
    reviews = df[df['asin'] == asin].to_dict('records')
    return reviews

def update_firestore(asin, details, reviews):
    if details is None or reviews is None:
        print(f"Skipping Firestore update for {asin} due to missing data.")
        return
    start = time.time()
    doc_ref = db.collection('products').document(asin)
    doc_ref.set({
        'details': details,
        'reviews': reviews
    }, merge=True)
    print(f"Updating Firestore for {asin} took {time.time() - start} seconds.")

def process_asin(asin):
    details = load_details_from_csv(asin)
    if details is None:
        print(f"Skipping {asin} due to failed details fetch.")
        return
    reviews = load_reviews_from_csv(asin)
    if reviews is None:
        print(f"Skipping {asin} due to failed reviews fetch.")
        return
    update_firestore(asin, details, reviews)

def main():
    for asin in asin_list:
        process_asin(asin)

main()
