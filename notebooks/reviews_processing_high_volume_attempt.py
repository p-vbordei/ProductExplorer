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
    from src.openai_utils import chat_completion_request, get_completion_list
    from src.investigations import update_investigation_status
except ImportError:
    from reviews_data_processing_utils import generate_batches, add_uid_to_reviews, aggregate_all_categories, attach_tags_to_reviews, quantify_category_data
    from firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, write_insights_to_firestore
    from openai_utils import chat_completion_request, get_completion_list
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
        reviewBatches = generate_batches(updatedReviewsList, max_tokens=8000)

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



        GPT_MODEL = 'gpt-3.5-turbo-16k'

        # Get responses from GPT
        async def main():
            responses = await get_completion_list(contentList, functions=marketFunctions, function_call="market", GPT_MODEL=GPT_MODEL)
            return responses

        responses = asyncio.run(main())

        # Process the responses
        evalResponses = []
        response_index = 0
        for batch in reviewBatches:
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
    print('Processing ', len(reviews), ' reviews')
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
    
    if not write_reviews_to_firestore(tagedReviews, db):
        logging.error("Error writing processed reviews to Firestore.")
        return

    if not update_investigation_status(investigationId, 'finishedReviews', db):
        logging.error(f"Error updating investigation status to 'finishedReviews'.")
        return

    logging.info(f"Reviews investigation for {investigationId} completed successfully.")










##########
# %%
investigationId = 'AN3fCSPOJVDTf95xiKVA'
db = initialize_firestore()
if not db:
    logging.error("Error initializing Firestore.")


if not update_investigation_status(investigationId, 'startedReviews', db):
    logging.error(f"Error updating investigation status to 'startedReviews'.")


reviews = get_clean_reviews(investigationId, db)
if not reviews:
    logging.error("Error getting clean reviews.")


# %%
reviewsList = reviews
# Allocate short Ids to reviews

updatedReviewsList, uid_to_id_mapping = add_uid_to_reviews(reviewsList)

# Prepare Review Batches
reviewBatches = generate_batches(updatedReviewsList, max_tokens=8000)

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



marketResponseHealFunction = [
            {
                "name": "formatEnforcementAndHeal",
                "description": "Check for errors in the input data and corrects them, ensuring the format is as bellow.",
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


functions = marketFunctions
functionCall = {"name": "market"}
# %%
GPT_MODEL = 'gpt-3.5-turbo-16k'

# Get responses from GPT
async def main():
    responses = await get_completion_list(contentList, functions=functions, function_call=functionCall, GPT_MODEL=GPT_MODEL)
    return responses

responses = asyncio.run(main())
# %%
# Process the responses
evalResponses = []
response_index = 0
for batch in reviewBatches:
    print(response_index)
    item = responses[response_index]
    data = item['function_call']['arguments']

    try:
        evalData = json.loads(data)
    except:
        print(item)
        print('Healing Function Activated at Json Loads for ', response_index, ' index')
        
        healingResponse =  chat_completion_request(
            messages= [{"role":"user", "content": f"Check this ouptput data and heal or correct any errors observed:{data} Response to be evaluated should be inside ['function_call']['arguments']."}],
            functions=marketResponseHealFunction,
            function_call={"name": "formatEnforcementAndHeal"},
            temperature=0,
            model=GPT_MODEL
            )
        resp = healingResponse.json()['choices']
        print(resp)
        parsed_resp =  resp[0]['message']['function_call']['arguments']
        try:
           evalData = json.loads(parsed_resp)
        except:
           print(evalData) 
           print(response_index)
           print("passing")
           pass
    evalResponses.append(evalData)
    response_index += 1
# %%

# Aggregate the responses
aggregatedResponses = aggregate_all_categories(evalResponses)

# %%


##################

useCaseFunction = [
    {
        "name": "useCaseFunction",
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
                }
            }
        }
    }
]

productComparisonFunction = [
    {
        "name": "productComparisonFunction",
        "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
        "parameters": {
            "type": "object",
            "properties": {
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
                }
            }
        }
    }
]

featureRequestFunction = [
    {
        "name": "featureRequestFunction",
        "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
        "parameters": {
            "type": "object",
            "properties": {
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
                }
            }
        }
    }
]

painPointsFunction = [
    {
        "name": "painPointsFunction",
        "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
        "parameters": {
            "type": "object",
            "properties": {
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
                }
            }
        }
    }
]

usageFrequencyFunction = [
    {
        "name": "usageFrequencyFunction",
        "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
        "parameters": {
            "type": "object",
            "properties": {
                "usageFrequency": {
                    "description": "Identifies the patterns of usage frequency discussed",
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
                }
            }
        }
    }
]

usageTimeFunction = [
    {
        "name": "usageTimeFunction",
        "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
        "parameters": {
            "type": "object",
            "properties": {
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
                }
            }
        }
    }
]

usageLocationFunction = [
    {
        "name": "usageLocationFunction",
        "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
        "parameters": {
            "type": "object",
            "properties": {
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
                }
            }
        }
    }
]

customerDemographicsFunction = [
    {
        "name": "customerDemographicsFunction",
        "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
        "parameters": {
            "type": "object",
            "properties": {
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
                }
            }
        }
    }
]

functionalJobFunction = [
    {
        "name": "functionalJobFunction",
        "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
        "parameters": {
            "type": "object",
            "properties": {
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
                }
            }
        }
    }
]

socialJobFunction = [
    {
        "name": "socialJobFunction",
        "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
        "parameters": {
            "type": "object",
            "properties": {
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
                }
            }
        }
    }
]

emotionalJobFunction = [
    {
        "name": "emotionalJobFunction",
        "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
        "parameters": {
            "type": "object",
            "properties": {
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
                }
            }
        }
    }
]

supportingJobFunction = [
    {
        "name": "supportingJobFunction",
        "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
        "parameters": {
            "type": "object",
            "properties": {
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
                    }
                }
            }
        }
    }
]


# %%

functionMapping = {
    "useCase": useCaseFunction,
    "productComparison": productComparisonFunction,
    "featureRequest": featureRequestFunction,
    "painPoints": painPointsFunction,
    "usageFrequency": usageFrequencyFunction,
    "usageTime": usageTimeFunction,
    "usageLocation": usageLocationFunction,
    "customerDemographics": customerDemographicsFunction,
    "functionalJob": functionalJobFunction,
    "socialJob": socialJobFunction,
    "emotionalJob": emotionalJobFunction,
    "supportingJob": supportingJobFunction
}

# %%

GPT_MODEL = 'gpt-3.5-turbo-16k'

responses = []
for key, function in functionMapping.items():
    contentList = [
        {"role": "user", "content": f"Process the results for key: {key}. Group together uid's from similar labels. Keep only what is distinct. Take a deep breath and work on this problem step-by-step. Limit the number of UIds if you need to in order to reach the token limit with no errors.\n {aggregatedResponses[key]}"}
    ]
    print({"name": function[0]["name"]})
    response = chat_completion_request(contentList, function, {"name": function[0]["name"]} ,temperature=0.5,model=GPT_MODEL)
    responses.append(response)



# %%
processedResults = []
for idx, response in enumerate(responses):
    key = list(aggregatedResponses.keys())[idx]
    resp = response.json()['choices']
    data = resp[0]['message']['function_call']['arguments']
    try:
        evalData = json.loads(data)
    except:
        healingResponse = chat_completion_request(
            messages=[{"role": "user", "content": f"Check this output data and heal or correct any errors observed: {data}. Response to be evaluated should be inside ['function_call']['arguments']."}],
            functions=marketResponseHealFunction,
            function_call={"name": "formatEnforcementAndHeal"},
            temperature=0,
            model=GPT_MODEL
        )
        resp = healingResponse.json()['choices']
        parsed_resp = resp[0]['message']['function_call']['arguments']
        try:
            evalData = json.loads(parsed_resp)
        except:
            evalData = {"error": "Unable to process the data"}
    processedResults.append(evalData)




# %%

processedData = dict(enumerate(processedResults))
# %%
dataOutput = {}
for item in processedResults:
    print(item)
    key = next(iter(item))
    for value in item[key]:
        label = value['label']
        dataOutput[key][label] = value

# %%
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
tagedReviews = attach_tags_to_reviews(updatedReviewsList, sortedResult)



# %%
# Sort the result dictionary by 'uid' keys
sortedResult = {k: processedData[k] for k in sorted(processedData)}


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


tagedReviews = attach_tags_to_reviews(updatedReviewsList, sortedResult)

for review in updatedReviewsList:
    # Get uid from the review
    uid = review.get('uid')
    
    # Fetch tags for the given uid from sortedResults
    tags = sortedResult.get(uid, {})
    
    # Add tags to the review
    review['tags'] = tags


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


# %%
