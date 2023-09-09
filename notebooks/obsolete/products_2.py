# %% [markdown]
# ## STRUCTURE
# - Read Products info
#     - Define data extraction function
#     - Extract the info from the products with GPT
#     - Process the results
#     - save to csv
# - Upload to sql
# 

# %%
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
import openai

import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored


load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


if os.getenv("OPENAI_API_KEY") is not None:
    print ("OPENAI_API_KEY is ready")
else:
    print ("OPENAI_API_KEY environment variable not found")

GPT_MODEL = "gpt-3.5-turbo"

# %%
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


# %%
def read_data(folder_path):
    product = pd.DataFrame()
    
    for file_name in os.listdir(folder_path):
        if file_name.startswith("asin"):
            file_path = os.path.join(folder_path, file_name)
            df = pd.read_csv(file_path)
            product = pd.concat([product, df])
    
    return product

# %%
products = read_data("/Users/vladbordei/Documents/Development/ProductExplorer/data/raw/RaisedGardenBed")
products['product_information.brand'] = products['product_information.brand'].apply(extract_brand_name)

# %%
# products_path = "./data/interim/products.csv"
product_path = "/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/products.csv"
products.to_csv(product_path, index=False)

# %%
product = products.copy()
product.reset_index(drop=True, inplace=True)

# %%
# asin_list_path = './data/external/asin_list.csv'
asin_list_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/external/asin_list.csv'
asin_list = pd.read_csv(asin_list_path)['asin'].tolist()

# %% [markdown]
# https://github.com/openai/openai-cookbook/blob/main/examples/How_to_call_functions_with_chat_models.ipynb

# %%
@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, functions=None, function_call=None, temperature=0, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + openai.api_key,
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

# %%
def remove_brand(strings, brand_column):
    cleaned_strings = []
    for string, brand in zip(strings, brand_column):
        cleaned_string = string.replace(brand, '').strip()
        cleaned_strings.append(cleaned_string)
    return cleaned_strings

product['product_information_title'] = remove_brand(product.title, product.product_information_brand)
product_tile = product['product_information_title'].iloc[0]
product_tile

# %%
# https://towardsdatascience.com/an-introduction-to-openai-function-calling-e47e7cd7680e
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
chatbot_responses = dict()


for i in product.index:
    print(i)
    title  = product['title'][i]
    asin  = product['asin'][i]
    bullets = product['feature_bullets'][i]

    # Get the product data
    print(asin)
    print(bullets)
    print(title)

    messages = [
        {"role": "user", "content": f"PRODUCT TITLE:``` {title} ``` PRODUCT BULLETS:```{bullets}```"},
    ]


    # Send the request to the LLM and get the response
    response =  chat_completion_request(
        messages=messages,
        functions=functions,
        function_call={"name": "describe_product"},
        temperature=0,
        model=GPT_MODEL
    )

    # Process the response and store in the dictionary
    chatbot_responses[asin] = response.json()["choices"]
    product.loc[i, 'product_description_data'] = chatbot_responses[asin]


# %%
for i in product.index:
    if isinstance(product.product_description_data[i], list):
        first_element = product.product_description_data[i][0]
        product.product_description_data[i] = first_element
    else:
        pass

# %%
for i in product.index:
    try:
        data = eval(product.product_description_data[i]['message']['function_call']['arguments'])
    except:
        data = product.product_description_data[i]['message']['function_call']['arguments']
    product['product_description_data'][i] = data

# %%
    # create a dictionary with key-value pairs for renaming
rename_dict = {
        'price.symbol': 'price_symbol',
        'badges.best_seller': 'bestsellers_rank',
        'badges.amazon_prime': 'badges_amazon_prime',
        'badges.amazon_сhoice': 'badges_amazon_choice',
        'reviews.total_reviews': 'reviews_total_reviews',
        'reviews.answered_questions': 'reviews_answered_questions',
        'reviews.rating': 'reviews_rating',
        'product_information.available_from': 'product_information_available_from',
        'product_information.available_from_utc': 'product_information_available_from_utc',
        'product_information.available_for_days': 'product_information_available_for_days',
        'product_information.available_for_months': 'product_information_available_for_months',
        'product_information.brand': 'product_information_brand',
        'product_information.department': 'product_information_department',
        'product_information.dimensions': 'product_information_dimensions',
        'product_information.manufacturer': 'product_information_manufacturer',
        'product_information.model_number': 'product_information_model_number',
        'product_information.qty_per_order': 'product_information_qty_per_order',
        'product_information.store_id': 'product_information_store_id',
        'product_information.weight': 'product_information_weight',
        'price.before_price': 'price_before_price',
        'price.currency': 'price_currency',
        'price.current_price': 'price_current_price',
        'price.discounted': 'price_discounted',
        'price.savings_amount': 'price_savings_amount',
        'price.savings_percent': 'price_savings_percent',
        'url': 'url',
        'title': 'title',
        'description': 'description',
        'feature_bullets': 'feature_bullets',
        'variants': 'variants',
        'categories': 'categories',
        'asin': 'asin',
        'item_available': 'item_available',
        'main_image': 'main_image',
        'total_images': 'total_images',
        'images': 'images',
        'total_videos': 'total_videos',
        'videos': 'videos',
        'delivery_message': 'delivery_message',
        'sponsored_products': 'sponsored_products',
        'also_bought': 'also_bought',
        'other_sellers': 'other_sellers',
        'product_description_data': 'product_description_data'
    }
    
product.rename(columns=rename_dict, inplace=True)

# %%
# products_path = "./data/interim/products_with_data.csv"
product_path = "/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/products_with_data.csv"
product.to_csv(product_path, index=False)





# %%
############# Introducere date in SQL ##############

# %%
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import select

# Create a SQLAlchemy engine
engine = create_engine('postgresql://postgres:mysecretpassword@localhost:5432/postgres')

metadata = MetaData()

def create_table(table_name, schema):
    try:
        table = Table(table_name, metadata, autoload_with=engine)
    except SQLAlchemyError:
        table = Table(table_name, metadata, schema, extend_existing=True)
        metadata.create_all(engine)

def insert_data(table_name, dataframe):
    # Convert DataFrame to a list of dictionaries
    data = dataframe.to_dict(orient='records')

    # Get the table
    table = Table(table_name, metadata, autoload_with=engine)

    # Insert the data
    with engine.begin() as connection:
        for row in data:
            connection.execute(table.insert(), row)

def delete_duplicates(table_name, column_name, id):
    with engine.begin() as connection:
        delete_query = text(f"""
            DELETE FROM {table_name} 
            WHERE {id} NOT IN (
                SELECT {id} 
                FROM {table_name} 
                GROUP BY {column_name} 
                HAVING COUNT(*) > 1
            )
        """)
        connection.execute(delete_query)

def get_duplicate_asins(table_name, column_name):
    with engine.begin() as connection:
        query = text(f"""
            SELECT {column_name}, COUNT(*) as count
            FROM {table_name} 
            GROUP BY {column_name}
            HAVING COUNT(*) > 1
        """)
        result = connection.execute(query)
        return result.fetchall()


# %%
from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'

    index = Column(Integer, primary_key=True)
    title = Column(Text)
    description = Column(Text)
    feature_bullets = Column(Text)
    variants = Column(Text)
    categories = Column(Text)
    asin = Column(String(10))
    url = Column(Text)
    reviews_total_reviews = Column(Integer)
    reviews_rating = Column(Float)
    reviews_answered_questions = Column(Integer)
    item_available = Column(Boolean)
    price_symbol = Column(Text)
    price_currency = Column(Text)
    price_current_price = Column(Float)
    price_discounted = Column(Boolean)
    price_before_price = Column(Float)
    price_savings_amount = Column(Float)
    price_savings_percent = Column(Float)
    bestsellers_rank = Column(Text)
    main_image = Column(Text)
    total_images = Column(Integer)
    images = Column(Text)
    total_videos = Column(Integer)
    videos = Column(Text)
    delivery_message = Column(Float)
    product_information_dimensions = Column(Float)
    product_information_weight = Column(Float)
    product_information_available_from = Column(Float)
    product_information_available_from_utc = Column(Float)
    product_information_available_for_months = Column(Integer)
    product_information_available_for_days = Column(Integer)
    product_information_manufacturer = Column(Float)
    product_information_model_number = Column(Float)
    product_information_department = Column(Float)
    product_information_qty_per_order = Column(Text)
    product_information_store_id = Column(Float)
    product_information_brand = Column(Text)
    badges_amazon_choice = Column(Boolean)
    badges_amazon_prime = Column(Boolean)
    badges_best_seller = Column(Boolean)
    sponsored_products = Column(Text)
    also_bought = Column(Text)
    other_sellers = Column(Text)
    product_description_data = Column(Text)

# Create the table
Base.metadata.create_all(engine)


# %%
# Insert data into the 'products' table
insert_data('products', product)

# Check if there are duplicates
duplicates = get_duplicate_asins('products', 'asin')
print(duplicates)

# Remove duplicates by ASIN from the 'products' table
delete_duplicates('products', 'asin', 'index')


#%%

# Add firestore imports
from google.cloud import firestore
from google.oauth2 import service_account

# %%
# Initialize Firestore DB
# Note: you must replace 'your-project-id' with your actual project id
# And also replace the path to your actual service account key json
credentials = service_account.Credentials.from_service_account_file(
    'path/to/your/serviceAccount.json')
db = firestore.Client(credentials=credentials, project='your-project-id')

# %% Add the following function
def upload_to_firestore(db, collection_name, data):
    # Check if collection exists
    if db.collection(collection_name).document('1').get().exists:
        print(f"{collection_name} collection already exists. Updating data...")
    else:
        print(f"Creating {collection_name} collection and uploading data...")

    # Upload each row of data as a new document
    for index, row in data.iterrows():
        doc_ref = db.collection(collection_name).document(str(index))
        doc_ref.set(row.to_dict())
    print(f"Data successfully uploaded to {collection_name} collection.")

# %% Replace the part where you save to csv with the following Firestore upload
# product_path = "/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/products_with_data.csv"
# product.to_csv(product_path, index=False)

upload_to_firestore(db, 'products', product)