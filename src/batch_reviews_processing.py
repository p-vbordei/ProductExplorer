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
    from src.reviews_data_processing_utils import process_datapoints, quantify_observations, generate_batches, add_uid_to_reviews, aggregate_all_categories, extractTagsForReview
    from src.firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, save_cluster_info_to_firestore, write_insights_to_firestore
    from src.openai_utils import get_completion_list_multifunction, chat_completion_request
    from src.reviews_clustering import cluster_reviews, label_clusters
    from src.investigations import update_investigation_status
except ImportError:
    from reviews_data_processing_utils import process_datapoints, quantify_observations, generate_batches, add_uid_to_reviews, aggregate_all_categories, extractTagsForReview
    from firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, save_cluster_info_to_firestore, write_insights_to_firestore
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
    {"role": "user", "content": f"Process the results from a function runing on multiple reviews batches. Group together uid's from simmilar labels. Keep only what is distinct.\n {aggregatedResponses}"}
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
sorted_result = {k: result[k] for k in sorted(result)}

print(sorted_result)


# %%



# RAMAS DE FACUT: DE SCRIS O FUNCTIE CARE TRECE PRIN FIECARE UID SI SALVEAZA INTR_UN CAMP TAGS Date astea

# Update the reviewsList to include tags
for reviewDict in updatedReviewsList:
    reviewUid = reviewDict['uid']
    tagsForReview = {}
    for data in aggregatedResponses:
        tags = extractTagsForReview(reviewUid, data)
        tagsForReview.update(tags)
    if tagsForReview:
        reviewDict['tags'] = tagsForReview


# %%
