# %%
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
import openai
import json

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
# Read data about the product

with open('/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/short_product_information.json') as file:
    json_string = file.read()
    general_product_data = json.loads(json_string)

# %%
#asin_list_path = './data/external/asin_list.csv'
asin_list_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/external/asin_list.csv'
asin_list = pd.read_csv(asin_list_path)['asin'].tolist()

# %%
attribute_clusters_with_percentage_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/attribute_clusters_with_percentage.csv'
attributes = pd.read_csv(attribute_clusters_with_percentage_path)

# %%
reviews_with_clusters_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/reviews_with_clusters.csv'
reviews_with_clusters = pd.read_csv(reviews_with_clusters_path)

# %%
attributes.drop(columns=['Unnamed: 0'], inplace=True)

# %%
set(attributes['Attribute'])

# %%
attributes.columns

# %%
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(12, 6))
sns.barplot(x=attributes[attributes['Attribute'] ==   'Issues']['attribute_percentage'], y=attributes[attributes['Attribute'] == 'Issues']['cluster_label'], data=attributes, ci=None, color='b')
plt.xlabel('Attribute Percentage (%)')
plt.ylabel('Attribute')
plt.title('Attributes by Attribute Percentage')
plt.show()

# %%
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(12, 6))
sns.barplot(x=attributes[attributes['Attribute'] ==   'Issues']['observation_count'], y=attributes[attributes['Attribute'] == 'Issues']['cluster_label'], data=attributes, ci=None, color='b')
plt.xlabel('Observation count')
plt.ylabel('Attribute')
plt.title('Attributes by Observation Count')
plt.show()

# %%
reviews_with_clusters.columns

# %%


# %%
set(attributes[attributes['Attribute'] == 'Issues']['cluster_label'])

# %%
set(reviews_with_clusters.loc[(reviews_with_clusters['Attribute'] == 'Issues') & (reviews_with_clusters['cluster_label'] == 'Flimsy and easily damaged'), 'Value'])

# %%
general_product_data

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
product_description = general_product_data

# %%
product_issues_list = list(set(attributes[attributes['Attribute'] == 'Issues']['cluster_label']))

# %%
product_issues_list

# %%
# product_issues_list.pop(1)

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


