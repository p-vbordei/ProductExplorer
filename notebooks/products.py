#%%
import os
import pandas as pd
import numpy as np
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

def update_investigation_status(investigation_id, new_status):
    investigation_ref = db.collection(u'investigations').document(investigation_id)
    investigation = investigation_ref.get()
    if investigation.exists:
        investigation_ref.update({
            'status': new_status,
            f'{new_status}_timestamp': firestore.SERVER_TIMESTAMP,
        })
        return True  # update was successful
    else:
        return False  # investigation does not exist
    



#%%
# user = "userId1"
investigation = "investigationId1"
update_investigation_status(investigation, "started_products")
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


###########################################################
#%%

# Update the Firestore database
for product in tqdm(products):
    doc_ref = db.collection('products').document(product['asin'])
    try:
        doc_ref.set(product, merge=True)  # Use set() with merge=True to update or create a new document
    except Exception as e:
        print(f"Error updating document {product['asin']}: {e}")


update_investigation_status(investigation, "finished_individual_products")
###########################################################################


# Ensure all the prices are floats
for product in tqdm(products):
    price = product['price']['current_price']
    if price is not None:
        price = float(price)
        product['price']['current_price'] = price

# Extract the prices and remove None values
prices = [product['price']['current_price'] for product in products if product['price']['current_price'] is not None]

# Calculate the median and round it
median_product_price = round(np.median(prices), 0)


# %%
product_summary_dict = {}
what_is_in_the_box_dict = {}
technical_facts_dict = {}
features_dict = {}
how_product_use_dict = {}
where_product_use_dict = {}
user_description_dict = {}
packaging_description_dict = {}
season_description_dict = {}
when_product_use_dict = {}



for product_item in products:
    asin = product_item['asin']
    data = product_item['product_description_data']

    product_summary_dict[asin] = data.get('Product Summary')
    what_is_in_the_box_dict[asin] = data.get('What is in the box?')
    technical_facts_dict[asin] = data.get('Technical Facts?')
    features_dict[asin] = data.get('Features')
    how_product_use_dict[asin] = data.get('How the product is used?')
    where_product_use_dict[asin] = data.get('Where the product is used?')
    user_description_dict[asin] = data.get('User Description?')
    packaging_description_dict[asin] = data.get('Packaging?')
    season_description_dict[asin] = data.get('Season?')
    when_product_use_dict[asin] = data.get('When the product is used?')

list_of_product_data_dictionaries = [product_summary_dict, what_is_in_the_box_dict, technical_facts_dict, features_dict, how_product_use_dict, where_product_use_dict, user_description_dict,season_description_dict,when_product_use_dict]


# %% [markdown]
# ### Product Summary

# %%
# https://towardsdatascience.com/an-introduction-to-openai-function-calling-e47e7cd7680e
functions = [
    {
        "name": "product_summary_function",
        "description": "Provide a detailed description of a product based on observations on simmilar products",
        "parameters": {
            "type": "object",
            "properties": {
                "product_summary": {
                    "type": "string",
                    "description": "Write a single product fact sheet summary of a product based on these observations from an ecommerce site, in 200 words. Exclude brand names."
                },
                "product_summary_outliers": {
                    "type": "string",
                    "description": "Identify if any outliers exist and explain them. Example: B09VBZZ9C8 (<asin>) is an outlier as it includes 3 mini magnetic drawing boards \
                                    instead of a single board, and B085Q3TLF8 stands out for its glowing in the dark feature."\
                }
            },
            "required": ["product_summary", "product_summary_outliers"]
        },
    }
]

# %%
messages = [
    {"role": "user", "content": f"```PRODUCT SUMMARIES:``` {product_summary_dict}"}
]

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=functions,
    function_call={"name": "product_summary_function"},
    temperature=0,
    model=GPT_MODEL
)

# Process the response and store in the dictionary

main_product_summary_response = response.json()["choices"]

# %%
main_product_summary_response

# %% [markdown]
# ### What is in the box

# %%
# https://towardsdatascience.com/an-introduction-to-openai-function-calling-e47e7cd7680e
functions = [
    {
        "name": "what_is_in_the_box",
        "description": "Provide a detailed description of what is in the box of a product based on knowledge of simmilar products",
        "parameters": {
            "type": "object",
            "properties": {
                "in_the_box": {
                    "type": "string",
                    "description": "Write a single what is in the box of a product based on these OBSERVATIONS. Select the most common values from OBSERVATIONS."
                },
                "in_the_box_outliers": {
                    "type": "string",
                    "description": "Identify if any outliers exist on  what is in the box of a product and explain them. If any products have something extra in the box, say what the ASIN is and what is diffrent"\
                }
            },
            "required": ["in_the_box", "in_the_box_outliers"]
        },
    }
]

# %%
messages = [
    {"role": "user", "content": f"{what_is_in_the_box_dict}"}
]

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=functions,
    function_call={"name": "what_is_in_the_box"},
    temperature=0,
    model=GPT_MODEL
)

# Process the response and store in the dictionary
main_product_what_is_in_the_box_response = response.json()["choices"]



# %% [markdown]
# ### Technical Facts

# %%
# https://towardsdatascience.com/an-introduction-to-openai-function-calling-e47e7cd7680e
functions = [
    {
        "name": "technical_facts_function",
        "description": "write the technical facts / details of a single product from the feat sheets of simmilar products",
        "parameters": {
            "type": "object",
            "properties": {
                "technical_facts": {
                    "type": "string",
                    "description": "Write a single what is in the box of a product based on these OBSERVATIONS. \
                        Select the most common values from OBSERVATIONS."
                },
                "technical_facts_outliers": {
                    "type": "string",
                    "description": "Identify if any outliers exist on  technical facts / details of a single product from the feat sheets of a product and explain them. Say what the ASIN is and what is diffrent"\
                }
            },
            "required": ["technical_facts", "technical_facts_outliers"]
        },
    }
]

# %%
messages = [
    {"role": "user", "content": f"{technical_facts_dict}"}
]

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=functions,
    function_call={"name": "technical_facts_function"},
    temperature=0,
    model=GPT_MODEL
)

# Process the response and store in the dictionary
main_product_technical_facts_response = response.json()["choices"]



# %% [markdown]
# ### Features

# %%
# https://towardsdatascience.com/an-introduction-to-openai-function-calling-e47e7cd7680e
functions = [
    {
        "name": "features_function",
        "description": "write the features of a single product from the feat sheets of simmilar products",
        "parameters": {
            "type": "object",
            "properties": {
                "features": {
                    "type": "string",
                    "description": """ Write the features of a single product from the fact sheets of a product \
                                    based on these OBSERVATIONS. Focus on the benefits that using the product brings. Example output: \
                                        "Learning disguised as play": "Makes learning fun and engaging",\
                                        "Portable and travel-friendly": "Easy to carry and use on the go",\
                                        "No eraser needed": "Effortless erasing and reusing",\
                                        "120 magnetic beads": "Provides ample space for creativity and learning",\
                                        "Easy to erase and reset": "Convenient and time-saving",\
                                        "Stylus stored at the bottom": "Ensures easy storage and transportation",\
                                        "Magnetized beads": "Allows for smooth drawing and tactile learning",\
                                        "Stylus pen": "Enables precise control and encourages proper grip" """
                },
                "features_outliers": {
                    "type": "string",
                    "description": "Identify if any features outliers exist and explain them. Say what the ASIN is and what is diffrent"\
                }
            },
            "required": ["features", "features_outliers"]
        },
    }
]

# %%
messages = [
    {"role": "user", "content": f"{features_dict}"}
]

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=functions,
    function_call={"name": "features_function"},
    temperature=0,
    model=GPT_MODEL
)

# Process the response and store in the dictionary
main_product_features_response = response.json()["choices"]



# %% [markdown]
# ### How to use the product

# %%
functions = [
    {
        "name": "how_product_use_function",
        "description": "write how a single product is used based on the observations  on simmilar products", 
        "parameters": {
            "type": "object",
            "properties": {
                "how_the_product_is_used": {
                    "type": "string",
                    "description": """ Write how a single product is used / can be used based on these \
                                    OBSERVATIONS  on simmilar products. Example output: \
                                    "The product is primarily used for drawing, \
                                    designing, creating, and playing with magnetic beads. \
                                    It can also be used for teaching children how to write and draw, \
                                    taking messages, completing classroom assignments, and practicing alphabets and numbers." """
                },
                "how_the_product_is_used_outliers": {
                    "type": "string",
                    "description": "Identify if any outliers exist on who the product is used and explain them. Say what the ASIN is and what is diffrent"\
                }
            },
            "required": ["how_the_product_is_used", "how_the_product_is_used_outliers"]
        },
    }
]

# %%
messages = [
    {"role": "user", "content": f"{how_product_use_dict}"}
]

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=functions,
    function_call={"name": "how_product_use_function"},
    temperature=0,
    model=GPT_MODEL
)

# Process the response and store in the dictionary
main_product_how_to_use_response = response.json()["choices"]



# %% [markdown]
# ### Where the product is used

# %%
functions = [
    {
        "name": "where_product_use_function",
        "description": "write where a single product is used based on the observations  on simmilar products", 
        "parameters": {
            "type": "object",
            "properties": {
                "where_the_product_is_used": {
                    "type": "string",
                    "description": """ Write where a single product is used based on these \
                                    OBSERVATIONS. Example output: \
                                    "Home, schools, classrooms, long drives, \
                                    doctor's offices, waiting for a flight, restaurants, on-the-go, and travel" """
                },
                "where_the_product_is_used_outliers": {
                    "type": "string",
                    "description": "Identify if any features outliers exist on where the product is used and explain them. Say what the ASIN is and what is diffrent"\
                }
            },
            "required": ["where_the_product_is_used", "where_the_product_is_used_outliers"]
        },
    }
]

# %%
messages = [
    {"role": "user", "content": f"{where_product_use_dict}"}
]

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=functions,
    function_call={"name": "where_product_use_function"},
    temperature=0,
    model=GPT_MODEL
)

# Process the response and store in the dictionary
main_product_where_to_use_response = response.json()["choices"]



# %% [markdown]
# ### User Description

# %%
functions = [
    {
        "name": "user_description_function",
        "description": "write who the user of a single product is based on the observations on simmilar products", 
        "parameters": {
            "type": "object",
            "properties": {
                "user_description": {
                    "type": "string",
                    "description": """ Write a user description of a single product based on these OBSERVATIONS. \
                                    Example output: \
                                    "This product is primarily designed for children, \
                                    including kids, toddlers, and preschoolers, with a broad age range from 3 years old \
                                    up to adults. """
                },
                "user_description_outliers": {
                    "type": "string",
                    "description": "Identify if any outliers exist on wheo the user of the product is and explain them. Say what the ASIN is and what is diffrent"\
                }
            },
            "required": ["user_description", "user_description_outliers"]
        },
    }
]

# %%
messages = [
    {"role": "user", "content": f"{user_description_dict}"}
]

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=functions,
    function_call={"name": "user_description_function"},
    temperature=0,
    model=GPT_MODEL
)

# Process the response and store in the dictionary
main_product_user_description_response = response.json()["choices"]

# %% [markdown]
# ### Packaging Description

# %%
functions = [
    {
        "name": "product_packaging_function",
        "description": "describe the packaging of a single product based on the observations on simmilar products", 
        "parameters": {
            "type": "object",
            "properties": {
                "product_packaging": {
                    "type": "string",
                    "description": "summarize the packaging of a single product based on these OBSERVATIONS. Don't repeat information and eleminate any brand names" 
                },
                "product_packaging_outliers": {
                    "type": "string",
                    "description": "Identify if any outliers exist on the product packaging and explain them. Say what the ASIN is and what is diffrent"
                }
            },
            "required": ["product_packaging", "product_packaging_outliers"]
        },
    }
]

# %%
messages = [
    {"role": "user", "content": f"{packaging_description_dict}"}
]

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=functions,
    function_call={"name": "product_packaging_function"},
    temperature=0,
    model=GPT_MODEL
)

# Process the response and store in the dictionary
main_product_packaging_description_response = response.json()["choices"]

# %% [markdown]
# ### Season Description

# %%
functions = [
    {
        "name": "product_seasonal_use_function",
        "description": "write where a single product is used based on the observations on simmilar products", 
        "parameters": {
            "type": "object",
            "properties": {
                "product_seasonal_use": {
                    "type": "string",
                    "description": "describe the seasonal use of a product based on these OBSERVATIONS." 
                },
                "product_seasonal_use_outliers": {
                    "type": "string",
                    "description": "Identify if any outliers exist on the season when the product is used and explain them. Say what the ASIN is and what is diffrent"\
                }
            },
            "required": ["product_seasonal_use", "product_seasonal_use_outliers"]
        },
    }
]

# %%
messages = [
    {"role": "user", "content": f"{season_description_dict}"}
]

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=functions,
    function_call={"name": "product_seasonal_use_function"},
    temperature=0,
    model=GPT_MODEL
)

# Process the response and store in the dictionary
main_product_season_to_use_response = response.json()["choices"]



# %% [markdown]
# ### When the product is used Description

# %%
functions = [
    {
        "name": "when_product_use_function",
        "description": "write where a single product is used based on the observations on simmilar products", 
        "parameters": {
            "type": "object",
            "properties": {
                "when_the_product_is_used": {
                    "type": "string",
                    "description": "describe when a product is used based on these OBSERVATIONS." 
                },
                "when_the_product_is_used_outliers": {
                    "type": "string",
                    "description": "Identify if any outliers exist on when the product is used and explain them. Say what the ASIN is and what is diffrent"\
                }
            },
            "required": ["when_the_product_is_used", "when_the_product_is_used_outliers"]
        },
    }
]

# %%
messages = [
    {"role": "user", "content": f"{when_product_use_dict}"}
]

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=functions,
    function_call={"name": "when_product_use_function"},
    temperature=0,
    model=GPT_MODEL
)

# Process the response and store in the dictionary
main_product_when_to_use_response = response.json()["choices"]



# %%
initial_responses = {}
initial_responses['product_summary'] = main_product_summary_response
initial_responses['what_is_in_the_box'] = main_product_what_is_in_the_box_response
initial_responses['technical_facts'] = main_product_technical_facts_response
initial_responses['features'] = main_product_features_response
initial_responses['how_product_use'] = main_product_how_to_use_response
initial_responses['where_product_use'] = main_product_where_to_use_response
initial_responses['user_description'] = main_product_user_description_response
initial_responses['packaging_description'] = main_product_packaging_description_response
initial_responses['season_description'] = main_product_season_to_use_response
initial_responses['when_product_use'] = main_product_when_to_use_response

# %%
product_data_interim ={}
for key in initial_responses.keys():
    product_data_interim[key] = eval(initial_responses[key][0]['message']['function_call']['arguments'])

#%%
product_data = {}
for main_key in product_data_interim.keys():
    for secondary_key in product_data_interim[main_key].keys():
        product_data[secondary_key] = product_data_interim[main_key][secondary_key]

# %%
product_data['median_product_price'] = median_product_price




general_product_keys_to_keep = ['Product Summary', 'product_summary','In_the_Box', 'in_the_box', 'technical_facts', 'features', 'how_the_product_is_used',  'where_the_product_is_used', 'user_description','median_product_price']

short_product_data = {}
for key in general_product_keys_to_keep:
    if key in product_data.keys():
        short_product_data[key] = product_data[key]

other_product_data_keys = set(product_data.keys()) - set(short_product_data.keys)

other_product_data = {}
for key in other_product_data_keys:
    if key in product_data.keys():
        short_product_data[key] = product_data[key]

data['short_product_data'] = short_product_data
data['other_product_data'] = other_product_data
# I need to write product data to investigations in the firebase

# %%
doc_ref = db.collection('investigations').document(investigation)
try:
    doc_ref.set(data, merge=True)  # Use set() with merge=True to update or create a new document
except Exception as e:
    print(f"Error saving investigation results with id {investigation}: {e}"
          
update_investigation_status(investigation, "finished_products")