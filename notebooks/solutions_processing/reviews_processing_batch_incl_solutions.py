# ##################
# reviews_processing.py
# %%
import asyncio
from tqdm import tqdm
import time
import logging
import pandas as pd
logging.basicConfig(level=logging.INFO)
import tiktoken
import json

try:
    from src import app
    from src.reviews_data_processing_utils import process_datapoints, quantify_observations, generate_batches, add_uid_to_reviews, aggregate_all_categories, attach_tags_to_reviews
    from src.firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, save_cluster_info_to_firestore, write_insights_to_firestore, get_product_data_from_investigation
    from src.openai_utils import get_completion_list_multifunction, chat_completion_request
    from notebooks.obsolete.reviews_clustering import cluster_reviews, label_clusters
    from src.investigations import update_investigation_status
except ImportError:
    from reviews_data_processing_utils import process_datapoints, quantify_observations, generate_batches, add_uid_to_reviews, aggregate_all_categories, attach_tags_to_reviews
    from firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, save_cluster_info_to_firestore, write_insights_to_firestore, get_product_data_from_investigation
    from openai_utils import get_completion_list_multifunction, chat_completion_request
    from reviews_clustering import cluster_reviews, label_clusters
    from investigations import update_investigation_status

# %%



def process_reviews_with_gpt(reviewsList, db):
    """
    Process reviews using GPT and extract insights.

    Parameters:
    - reviewsList (list): List of reviews to be processed.
    - db: Firestore database instance.

    Returns:
    - list: Updated reviews list with extracted insights.
    """
    try:
        # Allocate short Ids to reviews
        updatedReviewsList = add_uid_to_reviews(reviewsList)

        # Prepare Review Batches
        reviewBatches = generate_batches(updatedReviewsList, max_tokens=1000)

        # Generate Content List for Batches
        contentList = []
        for batch in reviewBatches:
            batch_review = f"\n\n <Review uIds>  will be followed by <Review Rating> and than by  `review text`:"
            batch_review += "\n\n".join([f"<{review_id}>\n,<{review_rating}>\n,`{review_text}`" for review_id, review_rating, review_text in batch])
            
            messages = [
                {"role": "user", "content": batch_review},
            ]
            contentList.append(messages)

        logging.info("Content list prepared.")

        """
        marketFunctions = [
            {
                "name": "market",
                "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "useCase": {
                            "description": "Identifies the specific use case",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        }
                                    }
                                }
                            }
                        },
                        "productComparison": {
                            "description": "Compare the product to competitors",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        }
                                    }
                                }
                            }
                        },
                        "featureRequest": {
                            "description": "Identifies the requested features or enhancements",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        }
                                    }
                                }
                            }
                        },
                        "painPoints": {
                            "description": "Identifies the different pain points, specific challenges or problems customers encountered",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        }
                                    }
                                }
                            }
                        },
                        "usageFrequency": {
                            "description": "Identifies the  patterns of usage frequency discussed",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        }
                                    }
                                }
                            }
                        },
                        "usageTime": {
                            "description": "Identifies when the product is used",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        }
                                    }
                                }
                            }
                        },
                        "usageLocation": {
                            "description": "Identifies where the product is used",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        }
                                    }
                                }
                            }
                        },
                        "customerDemographics": {
                            "description": "Identifies the different demographic segments",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        }
                                    }
                                }
                            }
                        },
                        "functionalJob": {
                            "description": "Identifies main tasks or problems the product solves",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        }
                                    }
                                }
                            }
                        },
                        "socialJob": {
                            "description": "Identifies how users want to be seen by others using the product",
                            "type": "array",
                            "items": {      
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        }
                                    }
                                }
                            }
                        },
                        "emotionalJob": {
                            "description": "Identifies the feelings or states users aim to achieve with the product",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                    },
                                    "description": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        }
                                    }
                                }
                            }
                        },
                        "supportingJob": {
                            "description": "Identifies the tasks or activities that aid the main function of the product",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        }
                                    }
                                }
                        }    }
                    }
                }
            }
        ]
        """

        # am dat print la functiile de mai sus pt a reduce numarul de spatii albe care erau luate drept tokens
        marketFunctions = [{'name': 'market', 'description': 'Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.', 'parameters': {'type': 'object', 'properties': {'useCase': {'description': 'Identifies the specific use case', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'productComparison': {'description': 'Compare the product to competitors', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'featureRequest': {'description': 'Identifies the requested features or enhancements', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'painPoints': {'description': 'Identifies the different pain points, specific challenges or problems customers encountered', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'usageFrequency': {'description': 'Identifies the  patterns of usage frequency discussed', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'usageTime': {'description': 'Identifies when the product is used', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'usageLocation': {'description': 'Identifies where the product is used', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'customerDemographics': {'description': 'Identifies the different demographic segments', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'functionalJob': {'description': 'Identifies main tasks or problems the product solves', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'socialJob': {'description': 'Identifies how users want to be seen by others using the product', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'emotionalJob': {'description': 'Identifies the feelings or states users aim to achieve with the product', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'description': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'supportingJob': {'description': 'Identifies the tasks or activities that aid the main function of the product', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}}}}]
        # Define function sets and function calls
        functionsList = [
            marketFunctions
        ]
        functionsCallList = [
            {"name": "market"}
        ]

        GPT_MODEL = 'gpt-3.5-turbo-16k'

        # Get responses from GPT
        async def main():
            responses = await get_completion_list_multifunction(contentList, functionsList, functionsCallList, GPT_MODEL=GPT_MODEL)
            return responses

        responses = asyncio.run(main())

        # Process the responses
        evalResponses = []
        response_index = 0
        for batch in reviewBatches:
            for function in functionsCallList:
                item = responses[response_index]
                data = item['function_call']['arguments']
                evalData = json.loads(data)
                evalResponses.append(evalData)
                response_index += 1

        # Aggregate the responses
        aggregatedResponses = aggregate_all_categories(evalResponses)

        # Update the reviewsList to include tags
        for reviewDict in updatedReviewsList:
            reviewUid = reviewDict['uid']
            tagsForReview = {}
            for data in aggregatedResponses:
                tags = extractTagsForReview(reviewUid, data)
                tagsForReview.update(tags)
            if tagsForReview:
                reviewDict['tags'] = tagsForReview

        return updatedReviewsList, aggregatedResponses

    except Exception as e:
        logging.error(f"Error in process_reviews_with_gpt: {e}")
        return None, None  # Return None in case of error

# %%


investigationId = 'XM32WugzchytIZr6NWyJ'

try:
    # Initialize Firestore
    db = initialize_firestore()
    logging.info("Initialized Firestore successfully.")
except Exception as e:
    logging.error(f"Error initializing Firestore: {e}")

try:
    # Get clean reviews
    reviewsList = get_clean_reviews(investigationId, db)  # Renaming to reviewsList for consistency
    logging.info("Retrieved clean reviews successfully.")
except Exception as e:
    logging.error(f"Error getting clean reviews: {e}")



# %%


# Allocate short Ids to reviews
updatedReviewsList, uid_to_id_mapping = add_uid_to_reviews(reviewsList)



# %%
# Prepare Review Batches
reviewBatches = generate_batches(updatedReviewsList, max_tokens=1000)

# Generate Content List for Batches
contentList = []
for batch in reviewBatches:
    batch_review = f"\n\n <Review uIds>  will be followed by <Review Rating> and than by  `review text`:"
    batch_review += "\n\n".join([f"<{review_id}>\n,<{review_rating}>\n,`{review_text}`" for review_id, review_rating, review_text in batch])
    
    messages = [
        {"role": "user", "content": batch_review},
    ]
    contentList.append(messages)


# am dat print la functiile de mai sus pt a reduce numarul de spatii albe care erau luate drept tokens
marketFunctions = [{'name': 'market', 'description': 'Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.', 'parameters': {'type': 'object', 'properties': {'useCase': {'description': 'Identifies the specific use case', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'productComparison': {'description': 'Compare the product to competitors', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'featureRequest': {'description': 'Identifies the requested features or enhancements', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'painPoints': {'description': 'Identifies the different pain points, specific challenges or problems customers encountered', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'usageFrequency': {'description': 'Identifies the  patterns of usage frequency discussed', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'usageTime': {'description': 'Identifies when the product is used', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'usageLocation': {'description': 'Identifies where the product is used', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'customerDemographics': {'description': 'Identifies the different demographic segments', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'functionalJob': {'description': 'Identifies main tasks or problems the product solves', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'socialJob': {'description': 'Identifies how users want to be seen by others using the product', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'emotionalJob': {'description': 'Identifies the feelings or states users aim to achieve with the product', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'description': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}, 'supportingJob': {'description': 'Identifies the tasks or activities that aid the main function of the product', 'type': 'array', 'items': {'type': 'object', 'properties': {'label': {'type': 'string'}, 'uid': {'type': 'array', 'items': {'type': 'number'}}}}}}}}]
# Define function sets and function calls
functionsList = [
    marketFunctions
]
functionsCallList = [
    {"name": "market"}
]

GPT_MODEL = 'gpt-3.5-turbo-16k'

# Get responses from GPT
async def main():
    responses = await get_completion_list_multifunction(contentList, functionsList, functionsCallList, GPT_MODEL=GPT_MODEL)
    return responses

responses = asyncio.run(main())

# %%

# Process the responses
evalResponses = []
response_index = 0
for batch in reviewBatches:
    for function in functionsCallList:
        item = responses[response_index]
        data = item['function_call']['arguments']
        evalData = json.loads(data)
        evalResponses.append(evalData)
        response_index += 1

# Aggregate the responses
aggregatedResponses = aggregate_all_categories(evalResponses)

# %%
# I will write a function for GPT that will cluster into distinct tags the tags from aggregatedResponses and place uids where they are the same

GPT_MODEL = 'gpt-3.5-turbo-16k'

messages = [
    {"role": "user", "content": f"Process the results from a function runing on multiple reviews batches. Group together uid's from simmilar labels. Keep only what is distinct. Take a deep breath and work on this problem step-by-step.\n {aggregatedResponses}"}
]

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=marketFunctions,
    function_call={"name": "market"},
    temperature=0.3,
    model=GPT_MODEL
)

# Process the response and store in the dictionary

singleResponse = response.json()["choices"]

##################
# %%
data = singleResponse[0]['message']['function_call']['arguments']
processedData = json.loads(data)

# %%
# Initialize an empty dictionary for the results
result = {}

# Iterate over each key-value pair in the processedData dictionary
for key, value_list in processedData.items():
    # For each key-value pair, iterate over the list of dictionaries
    for value in value_list:
        label = value['label']
        # For each dictionary in the list, iterate over the uid list
        for uid in value['uid']:
            # For each uid, check if it already exists in the results dictionary
            if uid in result:
                # If it exists, append the new tag
                if key in result[uid]:
                    result[uid][key].append(label)
                else:
                    result[uid][key] = [label]
            else:
                # If not, create a new entry
                result[uid] = {key: [label]}

# Sort the result dictionary by 'uid' keys
sortedResult = {k: result[k] for k in sorted(result)}

# %%
def attach_tags_to_reviews(updatedReviewsList, sortedResult):
    """
    This function adds tags from sortedResults to the reviews in updatedReviewsList based on the uid.
    
    Args:
    - updatedReviewsList (list): A list of dictionaries containing reviews.
    - sortedResults (dict): A dictionary with tags for each uid.
    
    Returns:
    - list: A list of dictionaries with the combined information.
    """
    for review in updatedReviewsList:
        # Get uid from the review
        uid = review.get('uid')
        
        # Fetch tags for the given uid from sortedResults
        tags = sortedResult.get(uid, {})
        
        # Add tags to the review
        review['tags'] = tags
    
    return updatedReviewsList

# Example usage
tagedReviews = attach_tags_to_reviews(updatedReviewsList, sortedResult)

# %%
# get the asin and review text for each uid
uid_to_asin = {review['uid']: review['asin'] for review in tagedReviews}
uid_to_text = {review['uid']: review['text'] for review in tagedReviews}
uid_to_raing = {review['uid']: review['rating'] for review in tagedReviews}

# %%
# Add asin to each uid
for key, value_list in processedData.items():
    for item in value_list:
        item['asin'] = [uid_to_asin[uid] for uid in item['uid']]

# Add rating to each uid
for key, value_list in processedData.items():
    for item in value_list:
        item['rating'] = [uid_to_raing[uid] for uid in item['uid']]

    
# %%
def quantify_category_data(inputData):
    processedData = {}
    
    for categoryKey, labels in inputData.items():
        categoryTotalObservations = sum([len(labelData['uid']) for labelData in labels])
        processedLabels = []
        
        for labelData in labels:
            labelObservations = len(labelData['uid'])
            labelPercentage = (labelObservations / categoryTotalObservations) * 100
            formattedLabelPercentage = int("{:.0f}".format(labelPercentage))

            
            # Calculate average rating for label
            averageRating = sum(labelData['rating']) / len(labelData['rating'])
            formattedAverageRating = float("{:.1f}".format(averageRating))
            
            processedLabelData = {
                'label': labelData['label'],
                'uid': labelData['uid'],
                'asin': list(set(labelData['asin'])),
                '#': labelObservations,
                '%': formattedLabelPercentage,
                '*': formattedAverageRating
            }
            
            processedLabels.append(processedLabelData)
        
        processedData[categoryKey] = processedLabels
    
    return processedData


# %%
quantifiedData = quantify_category_data(processedData)

# %%
# Add the text from the reviews to each label
uid_to_text = {review['uid']: review['text'] for review in tagedReviews}

for key, value_list in quantifiedData.items():
    for item in value_list:
        item['voiceOfCustomer'] = [uid_to_text[uid] for uid in item['uid']]


# %%
# Add id to each uid
quantifiedDataId = quantifiedData.copy()
for key, value_list in quantifiedDataId.items():
    for item in value_list:
        item['id'] = [uid_to_id_mapping[uid] for uid in item['uid']]

# %%
minimumQuantifiedData = {
    key: [{k: entry[k] for k in ['label', '#', '*']} for entry in value]
    for key, value in quantifiedData.items()
}


# %%
categoriesToInvestigate = ['productComparison', 'featureRequest', 'painPoints']
minimumVoiceOfCustomerInput = {
    key: [
        {
            k: entry[k] if k != 'uid' else entry[k][:10]
            for k in ['label', '#', '*', 'voiceOfCustomer', 'uid']
        }
        for entry in value
    ]
    for key, value in quantifiedData.items() if key in categoriesToInvestigate
}

remainingQuantifiedDataInput = {
    key: [{k: entry[k] for k in ['label', '#', '*',]} for entry in value]
    for key, value in quantifiedData.items() if key in quantifiedData.keys() - categoriesToInvestigate
}


# %%

from firebase_utils import get_product_data_from_investigation
# %%
try:
    productDescription = get_product_data_from_investigation(db, investigationId)
    logging.info("Retrieved product description successfully.")
except Exception as e:
    logging.error(f"Error getting product description: {e}")




# %%
problemStatementFunction = [
    {
        "name": "problem_statement_function",
        "description": "This function is designed to isolate and describe singular, primary issues with products being sold on Amazon, using data from customer complaints and the product's description. Be very detailed and specific.",
        "parameters": {
            "type": "object",
            "properties": {
                "problemStatements": {
                    "type": "array",
                    "description": "An array of problem statements, each containing problem identification, statement, and customer voice examples.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "problem_identification": {
                                "type": "string",
                                "description": "Identify the key problem or issue with the product."
                            },
                            "problem_statement": {
                                "type": "string",
                                "description": "Elaborate on the identified problem, providing a detailed statement based on observations made. Be sure to include the context of the observation. This should be within a range of 200 words."
                            },
                            "customer_voice_examples": {
                                "type": "array",
                                "description": "Select and provide quotes from customer complaints that further detail the problem and illustrate its impact. This should be up to 5 examples and within a range of 10 - 200 words.",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "uid": {
                                "type": "array",
                                "description": "List of all uids for the reviews that are related or can be to used to describe, inform, enhance the problem statement. They will be provided to the engineering team to help drive a solution to the problem.",
                                "items": {
                                    "type": "number"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
]

# %%
GPT_MODEL = "gpt-3.5-turbo-16k"

messages = [
    {"role": "user", "content": f"Using the provided customer feedback and product description data, identify issues or opportunities and write problem statements.  PRODUCT DESCRIPTION: {productDescription} \n PRODUCT OBSEVATIONS: {minimumVoiceOfCustomerInput}, \n WHAT CUSTOMERS REVIEW: {remainingQuantifiedDataInput}"}
]
# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=problemStatementFunction,
    function_call={"name": "problem_statement_function"},
    temperature=0.5,
    model=GPT_MODEL
)

# Process the response and store in the dictionary

singleResponse = response.json()["choices"]
print(response.json()['usage'])

data = singleResponse[0]['message']['function_call']['arguments']
problemsToBeInvestigated = json.loads(data)

problemsToBeInvestigated



#######
# %%

productImprovementFunction = [
    {
        "name": "production_line_improvement_function",
        "description": "Generate up to three product modification solutions that require changes to the production line, primary mould, or materials. These solutions are derived from customer feedback and the product's current specifications. Each solution should include a clear rationale and a step-by-step guide for implementation, ensuring thoroughness without resorting to non-standard technical jargon. All instructions should be easily understood by engineers in the relevant domain.",
        "parameters": {
            "type": "object",
            "properties": {
                "productImprovements": {
                    "type": "array",
                    "description": "An array of product improvements, each containing a title, implementation details for the engineer, and considerations.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Title": {
                                "type": "string",
                            },
                            "Details": {
                                "type": "string",
                            },
                            "Implementation": {
                                "type": "array",
                                "description": "List of changes to the production line that will improve the product.",
                                 "items": { 
                                    "type": "object",
                                    "properties": {
                                        "component": { "type": "string" },
                                        "change": { "type": "string" },
                                        "reason": { "type": "string" },
                                        "risk": { "type": "string" },
                                        "benefit": { "type": "string" },
                                        "notes": { "type": "string" }
                                    }
                        }}}
                    }
                }
            }
        }
    }
]

# %%

categoriesForProductImprovement = ['customerDemographics', 'useCase', 'functionalJob', 'usageLocation',]
functionalVoiceOfCustomerInput = {
    key: [
        {
            k: entry[k] if k != 'uid' else entry[k][:10]  # Limit the number of items in 'uid' to 10
            for k in ['label', '#', '*', 'voiceOfCustomer', 'uid']
        }
        for entry in value
    ]
    for key, value in quantifiedData.items() if key in categoriesForProductImprovement
}

# %%

GPT_MODEL = "gpt-3.5-turbo-16k"

messages = [
    {"role": "user", "content": f"PROBLEM STATEMENT: {problemsToBeInvestigated} \n PRODUCT DESCRIPTION: {productDescription} \n PRODUCT OBSEVATIONS: {functionalVoiceOfCustomerInput}, \n WHAT CUSTOMERS REVIEW: {minimumQuantifiedData}. "}
]

# %%

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=productImprovementFunction,
    function_call={"name": "production_line_improvement_function"},
    temperature=0.5,
    model=GPT_MODEL
)

# Process the response and store in the dictionary

singleResponse = response.json()["choices"]
print(response.json()['usage'])

data = singleResponse[0]['message']['function_call']['arguments']

try:
    proposedProductImprovements = json.loads(data)
except:
    proposedProductImprovements = eval(data)
    

proposedProductImprovements
# %%





packagingImprovementFunction = [
    {
        "name": "CostEffectiveImprovements",
        "description": "Generate up to ten cheap improvements",
        "parameters": {
            "type": "object",
            "properties": {
                "productImprovements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Title": {
                                "type": "string",
                            },
                            "Details": {
                                "type": "string",
                            },
                            "Implementation": {
                                "type": "array",
                                "description": "List of changes to the packaging or added items that will enhance the product.",
                                "items": { 
                                    "type": "object",
                                    "properties": {
                                        "component": { "type": "string" },
                                        "change": { "type": "string" },
                                        "reason": { "type": "string" },
                                        "benefit": { "type": "string" },
                                        "notes": { "type": "string" },
                                        "cost": { "type": "string" },
                                        "time": { "type": "string" }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
]



categoriesForPackagingImprovement = ['useCase', 'functionalJob', 'customerDemographics', 'socialJob', 'emotionalJob', 'supportingJob']

emotionalVoiceOfCustomerInput = {
    key: [
        {
            k: entry[k] if k != 'uid' else entry[k][:3]  # Limit the number of items in 'uid' to 10
            for k in ['label', '#', '*', 'voiceOfCustomer', 'uid']
        }
        for entry in value
    ]
    for key, value in quantifiedData.items() if key in categoriesForPackagingImprovement
}

remainingQuantifiedDataInput = {
    key: [{k: entry[k] for k in ['label', '#', '*',]} for entry in value]
    for key, value in quantifiedData.items() if key in quantifiedData.keys() - categoriesForPackagingImprovement
}
# %%

GPT_MODEL = "gpt-3.5-turbo-16k"

messages = [
    {"role": "user", "content": f"PRODUCT DESCRIPTION: {productDescription} \n PRODUCT OBSEVATIONS: {emotionalVoiceOfCustomerInput} \n WHAT CUSTOMERS REVIEW: {remainingQuantifiedDataInput}  \n "}
]

# %%

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=packagingImprovementFunction,
    function_call={"name": "CostEffectiveImprovements"},
    temperature=0.5,
    model=GPT_MODEL
)

# Process the response and store in the dictionary

singleResponse = response.json()["choices"]
print(response.json()['usage'])

data = singleResponse[0]['message']['function_call']['arguments']

try:
    proposedProductImprovements = json.loads(data)
except:
    proposedProductImprovements = eval(data)
    

proposedProductImprovements
# %%


- Problem Statements are identified and described for each of the clusters
- Solutions for the Problem Statements are created and clustered. They are presented as solutions prepared by junior engineers.
- Product Improvements are generated based on product understanding and previously presented solution clusters.
