# %% [markdown]
# # Scope: Trecerea de la problema la solutie

# %%
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
import openai
import json
# Helps asyncio run within Jupyter
import nest_asyncio

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

GPT_MODEL = "gpt-3.5-turbo-16k"

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
df_problem_statements_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/problem_statements.csv'
df_problem_statements = pd.read_csv(df_problem_statements_path)

# %%
attributes_data = attributes[['Attribute', 'cluster_label', 'positive_sentiment',
       'negative_sentiment','observation_count', 'rating_avg', 'percentage_of_observations_vs_total_number_per_attribute','percentage_of_observations_vs_total_number_of_reviews' ]]

# %%
general_product_data

# %%
# De redus in dimensionalitate pentru a putea fi folosit

attribute_summary = attributes.groupby('Attribute').agg(
    Total_Observations=('observation_count', 'sum'),
    Average_Positive_Sentiment=('positive_sentiment', 'mean'),
    Average_Negative_Sentiment=('negative_sentiment', 'mean'),
    Average_Rating=('rating_avg', 'mean')
).reset_index()

# Clusters with the highest positive sentiment
top_pos_sentiment = attributes.nlargest(3, 'positive_sentiment')

# Clusters with the highest negative sentiment
top_neg_sentiment = attributes.nlargest(3, 'negative_sentiment')

# Clusters with the most observations
most_observations = attributes.nlargest(3, 'observation_count')

# Clusters with the least observations
least_observations = attributes.nsmallest(3, 'observation_count')

highest_avg_pos_sentiment_attribute = attribute_summary.loc[attribute_summary['Average_Positive_Sentiment'].idxmax()]['Attribute']
highest_avg_neg_sentiment_attribute = attribute_summary.loc[attribute_summary['Average_Negative_Sentiment'].idxmax()]['Attribute']

observations_dict = {}
# observations_dict['attribute_summary'] = attribute_summary.to_dict('records')
observations_dict['top_pos_sentiment'] = top_pos_sentiment.to_dict('records')
observations_dict['top_neg_sentiment'] = top_neg_sentiment.to_dict('records')
observations_dict['most_observations'] = most_observations.to_dict('records')
observations_dict['least_observations'] = least_observations.to_dict('records')
observations_dict['highest_avg_pos_sentiment_attribute'] = highest_avg_pos_sentiment_attribute
observations_dict['highest_avg_neg_sentiment_attribute'] = highest_avg_neg_sentiment_attribute

# %%
product_improvement_function = [
    {
        "name": "product_improvement_function",
        "description": "This function is designed to provide engineering solutions to address the primary issues with a product. The function uses the data from customer complaints and the product's description to propose technical product improvements. The Implementation Details  should be concise, yet comprehensive, explaining the rationale behind the solution and step-by-step instructions for carrying out the implementation. It should not contain jargon or technical terms that are not commonly understood by engineers in the relevant field.",
        "parameters": {
            "type": "object",
            "properties": {
                "Product Improvement 1": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the first proposed product improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the first improvement solution, including specific instructions for implementation by an engineer."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Considerations"]
                },
                "Product Improvement 2": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the second proposed product improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the second improvement solution, including specific instructions for implementation by an engineer."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Considerations"]
                },
                "Product Improvement 3": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the third proposed product improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "AA detailed, 200-word description of the third improvement solution, including specific instructions for implementation by an engineer."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Considerations"]
                },
                "Product Improvement 4": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the fourth proposed product improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the fourth improvement solution, including specific instructions for implementation by an engineer."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Considerations"]
                },
                "Product Improvement 5": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the fifth proposed product improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the fifth improvement solution, including specific instructions for implementation by an engineer."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Considerations"]
                },
                "Product Improvement 6": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the sixth proposed product improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the sixth improvement solution, including specific instructions for implementation by an engineer."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Considerations"]
                },
                "Product Improvement 7": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the seventh proposed product improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the seventh improvement solution, including specific instructions for implementation by an engineer."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Considerations"]
                },
            },
            "required": ["Product Improvement 1", "Product Improvement 2", "Product Improvement 3", "Product Improvement 4", "Product Improvement 5", "Product Improvement 6", "Product Improvement 7"]
        }
    }
]



# %%
product_sustainability_function = [
    {
        "name": "product_sustainability_function",
        "description": "This function is designed to provide economically feasible and sustainability enhancing solutions for a product. The function uses data from customer feedback, product description, and environmental impact analysis to propose product improvements. The Implementation Details should be concise and comprehensive, explaining the rationale behind the solution and step-by-step instructions for carrying out the implementation. It should avoid jargon or technical terms not commonly understood by engineers in the relevant field.",
        "parameters": {
            "type": "object",
            "properties": {
                "Sustainable Improvement 1": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the first proposed sustainable improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the first sustainability solution, including specific instructions for implementation by an engineer."
                        },
                        "Economic Feasibility": {
                            "type": "string",
                            "description": "A brief analysis of the economic feasibility of the proposed solution."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Economic Feasibility", "Considerations"]
                },
                "Sustainable Improvement 2": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the second proposed sustainable improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the second sustainability solution, including specific instructions for implementation by an engineer."
                        },
                        "Economic Feasibility": {
                            "type": "string",
                            "description": "A brief analysis of the economic feasibility of the proposed solution."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Economic Feasibility", "Considerations"]
                },
                "Sustainable Improvement 3": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the third proposed sustainable improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the third sustainability solution, including specific instructions for implementation by an engineer."
                        },
                        "Economic Feasibility": {
                            "type": "string",
                            "description": "A brief analysis of the economic feasibility of the proposed solution."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Economic Feasibility", "Considerations"]
                },
                "Sustainable Improvement 4": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the fourth proposed sustainable improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the fourth sustainability solution, including specific instructions for implementation by an engineer."
                        },
                        "Economic Feasibility": {
                            "type": "string",
                            "description": "A brief analysis of the economic feasibility of the proposed solution."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Economic Feasibility", "Considerations"]
                },
                "Sustainable Improvement 5": {
                    "type": "object",
                    "properties": {
                        "Title": {
                            "type": "string",
                            "description": "The title or short description of the fifth proposed sustainable improvement."
                        },
                        "Implementation Details for the engineer": {
                            "type": "string",
                            "description": "A detailed, 200-word description of the fifth sustainability solution, including specific instructions for implementation by an engineer."
                        },
                        "Economic Feasibility": {
                            "type": "string",
                            "description": "A brief analysis of the economic feasibility of the proposed solution."
                        },
                        "Considerations": {
                            "type": "string",
                            "description": "Considerations and potential challenges in the implementation of the proposed solution."
                        }
                    },
                    "required": ["Title", "Implementation Details for the engineer", "Economic Feasibility", "Considerations"]
                }
            },
            "required": ["Sustainable Improvement 1", "Sustainable Improvement 2", "Sustainable Improvement 3", "Sustainable Improvement 4", "Sustainable Improvement 5"]
        }
    }
]


# %%
problem = df_problem_statements['problem_statement']
messages = [
    {"role": "user", "content": f"PROBLEM STATEMENT: {problem} ,PRODUCT DESCRIPTION: {general_product_data} , ANALYSIS: {attributes_data}"}
]

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions= product_improvement_function,
    function_call={"name": "product_improvement_function"},
    temperature=0.5,
    model=GPT_MODEL
)

# Process the response and store in the dictionary
chat_response = response.json()["choices"][0]
print(chat_response)

# %%
data = eval(chat_response['message']['function_call']['arguments'])

# %%
data

# %%
problem = df_problem_statements['problem_statement']
messages = [
    {"role": "user", "content": f"PROBLEM STATEMENT: {problem} ,PRODUCT DESCRIPTION: {general_product_data} , ANALYSIS: {attributes_data}"}
]

# Send the request to the LLM and get the response
sustainability_response =  chat_completion_request(
    messages=messages,
    functions= product_sustainability_function,
    function_call={"name": "product_sustainability_function"},
    temperature=0.5,
    model=GPT_MODEL
)

# Process the response and store in the dictionary
sustainability_chat_response = sustainability_response.json()["choices"][0]
print(sustainability_chat_response)

# %%
sustainable_data = eval(sustainability_chat_response['message']['function_call']['arguments'])

# %%
sustainable_data

# %%


# %%
data = eval(chat_response['message']['function_call']['arguments'])

# %%
data

# %%
set(attributes_data['Attribute'])


# %%
attributes_data[attributes_data['Attribute'] == 'Buyer Motivation']

# %%
attributes_data[attributes_data['Attribute'] == 'Colors']

# %%
attributes_data['observation_count'].sum()

# %%
attributes_data.sort_values(by='percentage_of_observations_vs_total_number_of_reviews', ascending=False)


