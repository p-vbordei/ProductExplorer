#%%
import os
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
import asyncio
import aiofiles
import nest_asyncio
from pathlib import Path


load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GPT_MODEL = "gpt-3.5-turbo"

import json
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials, firestore

# Firestore details
cred_path = '/Users/vladbordei/Documents/Development/ProductExplorer/notebooks/productexplorerdata-firebase-adminsdk-ulb3d-465f23dff3.json'

# Initialize Firestore
cred = credentials.Certificate(cred_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

import openai
import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt

if OPENAI_API_KEY is not None:
    print("OPENAI_API_KEY is ready")
else:
    print("OPENAI_API_KEY environment variable not found")

#%%

def extract_brand_name(string):
    if isinstance(string, str) and ("Brand: " in string or "Visit the " in string):
        try:
            if "Brand: " in string:
                brand_name = string.split("Brand: ")[1]
            else:
                brand_name = string.split("Visit the ")[1]
            brand_name = brand_name.replace("Store", "").strip()
            return brand_name
        except IndexError:
            pass
    return string

def remove_brand(strings, brand_column):
    cleaned_strings = []
    for string, brand in zip(strings, brand_column):
        cleaned_string = string.replace(brand, '').strip()
        cleaned_strings.append(cleaned_string)
    return cleaned_strings


#%%


def get_asins_from_investigation(investigation_id):
    # Retrieve the investigation from Firestore
    investigation_ref = db.collection(u'investigations').document(investigation_id)
    investigation = investigation_ref.get()

    if investigation.exists:
        # Retrieve the asins from the investigation
        asins = investigation.get('asins')
        return asins
    else:
        print('Investigation does not exist')
        return None

def get_product_details_from_asin(asin):
    # Retrieve the product details from Firestore
    product_ref = db.collection('products').document(asin)
    product = product_ref.get()

    if product.exists:
        product_details = product.get('details')
        return product_details
    else:
        print(f'No product details found for ASIN {asin}')
        return None

def get_investigation_and_product_details(investigation_id):
    asins = get_asins_from_investigation(investigation_id)
    products = []

    if asins is not None:
        for asin in asins:
            product_details = get_product_details_from_asin(asin)
            if product_details is not None:
                products.append(product_details)

    return products


#%%
@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, functions=None, function_call=None, temperature=0, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + OPENAI_API_KEY,
    }
    json_data = {"model": model, "messages": messages, "temperature": temperature}
    if functions is not None:
        json_data.update({"functions": functions})
    if function_call is not None:
        json_data.update({"function_call": function_call})
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


#%%
# user = "userId1"
investigation = "investigationId1"
products= get_investigation_and_product_details("investigationId1")


#%%

functions = [
    {
        "name": "describe_product",
        "description": "Provide a detailed description of a product",
        "parameters": {
            "type": "object",
            "properties": {
                "Product Summary": {
                    "type": "string",
                    "description": "A brief summary of the product in 200 words"
                },
                "What is in the box": {
                    "type": "string",
                    "description": "Contents of the product package. Example: one micro USB charging cable, one 3.5mm auxiliary cable, and a user manual"
                },
                "Technical Facts": {
                    "type": "string",
                    "description": "Technical details about the product. Example: water-resistant body made from high-quality ABS plastic, stainless steel, BPA-free, lead-free, synthetic leather"
                },
                "Features": {
                    "type": "string",
                    "description": "Features of the product. Example: water-resistant design, excellent bounce consistency, suitable for both indoor and outdoor use "
                },
                "How the product is used": {
                    "type": "string",
                    "description": "Information about what the product is used for or about how the product is used. Example: doodling, practicing letters/shapes, playing games"
                },
                "Where the product is used": {
                    "type": "string",
                    "description": "Suggested locations or situations where the product can be used. Example: car, restaurant, garden, public parks"
                },
                "User Description": {
                    "type": "string",
                    "description": "Description of the user for the product. Example: children, preschoolers,  basketball players, mothers, office workers"
                },
                "Packaging": {
                    "type": "string",
                    "description": "Description of the product's packaging. Example: sturdy recyclable box, wrapped in plastic, great for gifting"
                },
                "Season": {
                    "type": "string",
                    "description": "Season or time of year when the product is typically used. Example: fall and winter"
                },
                "When the product is used": {
                    "type": "string",
                    "description": "Time of day or week when the product is typically used. Example: early in the morning, in the weekend"
                }
            },
            "required": ["Product Summary", "Features"]
        },
    }
]

# %%
# GPT CALL
# THIS CAN BE DONE IN ASYNC

chatbot_responses = dict()


for product in products:
    clean_brand = extract_brand_name(product['product_information']['brand'])
    product['clean_brand'] = clean_brand
    title = product.get('title')
    clean_title = remove_brand(title, clean_brand)
    product['clean_title'] = clean_title  # assuming you want to update the title in the product dictionary
    if product.get('investigations_list') is not None:
        product['investigations_list'].append(investigation)
    else:
        product['investigations_list'] = [investigation] 
    
    title = clean_title
    asin = product['asin']
    bullets = product['feature_bullets']

    print(asin)
    print(bullets)
    print(title)

    messages = [
        {"role": "user", "content": f"PRODUCT TITLE:``` {title} ``` PRODUCT BULLETS:```{bullets}```"},
    ]

    response = chat_completion_request(
        messages=messages,
        functions=functions,
        function_call={"name": "describe_product"},
        temperature=0,
        model=GPT_MODEL
    )

    if response.status_code == 200:
        response = response.json()
        print(response)
        product['product_description_data'] = response
    else:
        print("Unable to generate ChatCompletion response")
        print(f"Response: {response}")


#%%

def clean_description_data(data):
  if isinstance(data, list):
    return data[0]
  return data

# %%
for product in products:
  # Clean the description data
  product['clean_product_description_data'] = clean_description_data(product['product_description_data'])
  data = eval(product['clean_product_description_data']['choices'][0]['message']['function_call']['arguments'])
  product['clean_product_description_data'] = data


#########
#%%

# Update the Firestore database
for product in tqdm(products):
    doc_ref = db.collection('products').document(product['asin'])
    try:
        doc_ref.set(product, merge=True)  # Use set() with merge=True to update or create a new document
    except Exception as e:
        print(f"Error updating document {product['asin']}: {e}")


