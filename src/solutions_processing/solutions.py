# %%
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
import openai
import json
import logging

import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored


load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
HUGGINGFACEHUB_API_TOKEN = os.getenv('HUGGINGFACEHUB_API_TOKEN')

if os.getenv("OPENAI_API_KEY") is not None:
    print ("OPENAI_API_KEY is ready")
else:
    print ("OPENAI_API_KEY environment variable not found")

GPT_MODEL = "gpt-3.5-turbo"
INVESTIGATION = "investigationId2"

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


# %%

################## GPT FUNCTIONS ####################

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



############### FIREBASE FUNCTIONS ###############

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


def get_reviews_from_asin(asin):
    # Retrieve the reviews from Firestore
    reviews_query = db.collection('products').document(asin).collection('reviews').stream()

    # Store all reviews in a list
    product_reviews = []
    for review in reviews_query:
        product_reviews.append(review.to_dict())

    if product_reviews:
        return product_reviews
    else:
        print(f'No product reviews found for ASIN {asin}')
        return None


def get_investigation_and_reviews(investigation_id):
    asins = get_asins_from_investigation(investigation_id)
    reviews_list = []

    if asins is not None:
        for asin in asins:
            asin_reviews = get_reviews_from_asin(asin)
            if asin_reviews is not None:
                reviews_list.append(asin_reviews)
    return reviews_list


def get_short_product_data_from_investigation(investigation_id):
    # Retrieve the investigation from Firestore
    investigation_ref = db.collection(u'investigations').document(investigation_id)
    investigation = investigation_ref.get()

    if investigation.exists:
        # Retrieve the asins from the investigation
        short_product_data = investigation.get('short_product_data')
        return short_product_data
    else:
        print('Investigation does not exist')
        return None



########## DATA ACQUISITION ##############



# %%
# Read data about the product


update_investigation_status(INVESTIGATION, "started_solutions_processing")
asins_list = get_asins_from_investigation(INVESTIGATION)
product_description = get_short_product_data_from_investigation(INVESTIGATION)


# %%
attribute_clusters_with_percentage_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/attribute_clusters_with_percentage.csv'
attributes = pd.read_csv(attribute_clusters_with_percentage_path)

# %%
reviews_with_clusters_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/reviews_with_clusters.csv'
reviews_with_clusters = pd.read_csv(reviews_with_clusters_path)



#################################################
############### PROBLEM STATEMENT ###############


# %%
try:
    attributes.drop(columns=['Unnamed: 0'], inplace=True)
except:
    pass


# %%
problem_statement_function = [
    {
        "name": "problem_statement_function",
        "description": """This function is designed to isolate and describe a singular, primary issue with a product being sold on Amazon, using the data from customer complaints and the product's description. 
        Example Output:     
            "problem_identification": "Lack of durability and insufficient planting space",
            "problem_statement": "The garden beds are perceived as flimsy and require additional support. They also appear to provide less planting space than customers expected.",
            "customer_voice_examples": [
                "The garden beds are flimsy and require additional support with wood framing.", 
                "Wished for more room for additional grow beds", 
                "Oval-shaped box loses a little planting space, but not worried about it at this time"
                ]""",
        "parameters": {
            "type": "object",
            "properties": {
                "problem_identification": {
                    "type": "string",
                    "description": "From the given data, identify and articulate the key problem or issue with the product." 
                },
                "problem_statement": {
                    "type": "string",
                    "description": "Elaborate on the identified problem, providing a detailed statement based on the observations made. This should be within a range of 200 words." 
                },
                "customer_voice_examples": {
                    "type": "string",
                    "description": "Select and provide quotes from customer complaints which further detail the problem and illustrate its impact. This should be up to 10 examples and within a range of 10 - 200 words." 
                },
            },
            "required": ["problem_identification", "problem_statement", "customer_voice_examples"]
        }
    }
]


# %%
product_issues_list = list(set(attributes[attributes['Attribute'] == 'Issues']['cluster_label']))


# %%
for issue in product_issues_list:
    customer_voice_examples = list(set(reviews_with_clusters.loc[(reviews_with_clusters['Attribute'] == 'Issues') & (reviews_with_clusters['cluster_label'] == issue), 'Value']))
    print (issue)
    print (customer_voice_examples)

# %%
problem_statements = []
for issue in product_issues_list:
    customer_voice_examples = list(set(reviews_with_clusters.loc[(reviews_with_clusters['Attribute'] == 'Issues') & (reviews_with_clusters['cluster_label'] == issue), 'Value']))

    messages = [
        {"role": "user", "content": f"ISSUE {issue} CUSTOMER VOICE EXAMPLES: {customer_voice_examples} AND PRODUCT DESCRIPTION: {product_description}"}
    ]

    # Send the request to the LLM and get the response
    response =  chat_completion_request(
        messages=messages,
        functions=problem_statement_function,
        function_call={"name": "problem_statement_function"},
        temperature=0,
        model=GPT_MODEL
    )

    # Process the response and store in the dictionary
    chat_response = response.json()["choices"][0]
    problem_statements.append(chat_response)

# %%
df_problem_statements = pd.DataFrame(product_issues_list, columns=['cluster_label'])
df_problem_statements['Attribute'] = 'Issues'
df_problem_statements

# %%
eval_responses = []
for item in problem_statements:
    data = item['message']['function_call']['arguments']
    # Replace 'null' with 'None' in the data string before evaluation
    data = data.replace('null', 'None')
    eval_data = eval(data)
    eval_responses.append(eval_data)

df_problem_statements['problem_statement'] = eval_responses

# %%
df_problem_statements_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/problem_statements.csv'
df_problem_statements.to_csv(df_problem_statements_path, index = False)

# %%
