# %%
import pandas as pd
import numpy as np
import requests
import logging
logging.basicConfig(level=logging.INFO)

try:
    from src import app, connex_app
    from src.firebase_utils import initialize_firestore, get_product_data_from_investigation
    from src.investigations import start_investigation, get_asins_from_investigation
    from src.data_acquisition import execute_data_acquisition
    from src.products_processing import run_products_investigation
    from src.reviews_processing import run_reviews_investigation
    from src.users import  update_investigation_status
    from src.openai_utils import get_completion_list
except ImportError:
    from firebase_utils import initialize_firestore,  get_product_data_from_investigation
    from investigations import start_investigation, get_asins_from_investigation
    from data_acquisition import execute_data_acquisition
    from products_processing import run_products_investigation
    from reviews_processing import run_reviews_investigation
    from users import  update_investigation_status
    from openai_utils import get_completion_list






########## DATA ACQUISITION ##############



# %%
# Read data about the product

investigationId = 'investigation_1'

try:
    # Initialize Firestore
    db = initialize_firestore()
    logging.info("Initialized Firestore successfully.")
except Exception as e:
    logging.error(f"Error initializing Firestore: {e}")

try:
    update_investigation_status(investigationId, 'startedProblemStatements', db)
except Exception as e:
    logging.error(f"Error updating investigation status to 'startedProblemStatements': {e}")
    pass

try:
    product_description = get_product_data_from_investigation(investigationId)
    logging.info("Retrieved product description successfully.")
except Exception as e:
    logging.error(f"Error getting product description: {e}")






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
