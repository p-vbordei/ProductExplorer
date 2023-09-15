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
    from src.reviews_data_processing_utils import generate_batches, add_uid_to_reviews, aggregate_all_categories, attach_tags_to_reviews, quantify_category_data
    from src.firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, write_insights_to_firestore
    from src.openai_utils import get_completion_list_multifunction, chat_completion_request
    from src.investigations import update_investigation_status
except ImportError:
    from reviews_data_processing_utils import generate_batches, add_uid_to_reviews, aggregate_all_categories, attach_tags_to_reviews, quantify_category_data
    from firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, write_insights_to_firestore
    from openai_utils import get_completion_list_multifunction, chat_completion_request
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
        updatedReviewsList, uid_to_id_mapping = add_uid_to_reviews(reviewsList)

        # Prepare Review Batches
        reviewBatches = generate_batches(updatedReviewsList, max_tokens=10000)

        # Generate Content List for Batches
        contentList = []
        for batch in reviewBatches:
            batch_review = f"\n\n <Review uIds>  will be followed by <Review Rating> and than by  `review text`:"
            batch_review += "\n\n".join([f"<{review_id}>\n,<{review_rating}>\n,`{review_text}`" for review_id, review_rating, review_text in batch])
            
            messages = [
                {"role": "user", "content": batch_review},
            ]
            contentList.append(messages)



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
 
        data = singleResponse[0]['message']['function_call']['arguments']
        processedData = json.loads(data)


        result = {}
        for key, value_list in processedData.items():
            for value in value_list:
                label = value['label']
                for uid in value['uid']:
                    if uid in result:
                        if key in result[uid]:
                            result[uid][key].append(label)
                        else:
                            result[uid][key] = [label]
                    else:
                        result[uid] = {key: [label]}

        # Sort the result dictionary by 'uid' keys
        sortedResult = {k: result[k] for k in sorted(result)}

        tagedReviews = attach_tags_to_reviews(updatedReviewsList, sortedResult)


        # get the asin and review text for each uid
        uid_to_asin = {review['uid']: review['asin'] for review in tagedReviews}
        uid_to_text = {review['uid']: review['text'] for review in tagedReviews}
        uid_to_raing = {review['uid']: review['rating'] for review in tagedReviews}

        # Add asin to each uid
        for key, value_list in processedData.items():
            for item in value_list:
                item['asin'] = [uid_to_asin[uid] for uid in item['uid']]

        # Add rating to each uid
        for key, value_list in processedData.items():
            for item in value_list:
                item['rating'] = [uid_to_raing[uid] for uid in item['uid']]

        quantifiedData = quantify_category_data(processedData)

        # Add the text from the reviews to each label
        uid_to_text = {review['uid']: review['text'] for review in tagedReviews}

        for key, value_list in quantifiedData.items():
            for item in value_list:
                item['voiceOfCustomer'] = [uid_to_text[uid] for uid in item['uid']]


        # Add id to each uid
        quantifiedDataId = quantifiedData.copy()
        for key, value_list in quantifiedDataId.items():
            for item in value_list:
                item['id'] = [uid_to_id_mapping[uid] for uid in item['uid']]


        return tagedReviews, quantifiedDataId

    except Exception as e:
        logging.error(f"Error in process_reviews_with_gpt: {e}")
        return None, None  # Return None in case of error

# %%




def run_reviews_investigation(investigationId: str) -> None:
    db = initialize_firestore()
    if not db:
        logging.error("Error initializing Firestore.")
        return

    if not update_investigation_status(investigationId, 'startedReviews', db):
        logging.error(f"Error updating investigation status to 'startedReviews'.")
        return

    reviews = get_clean_reviews(investigationId, db)
    if not reviews:
        logging.error("Error getting clean reviews.")
        return

    tagedReviews, quantifiedDataId = process_reviews_with_gpt(reviews, db)
    if not tagedReviews or not quantifiedDataId:
        logging.error("Error processing reviews with GPT.")
        return
    
    if not write_insights_to_firestore(investigationId, quantifiedDataId, db):
        logging.error("Error writing quantified data to Firestore.")
        return
    
    if not write_reviews_to_firestore(investigationId, tagedReviews, db):
        logging.error("Error writing processed reviews to Firestore.")
        return

    if not update_investigation_status(investigationId, 'finishedReviews', db):
        logging.error(f"Error updating investigation status to 'finishedReviews'.")
        return

    logging.info(f"Reviews investigation for {investigationId} completed successfully.")

