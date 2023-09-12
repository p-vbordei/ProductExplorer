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
    from src.openai_utils import get_completion_list_multifunction
    from src.reviews_clustering import cluster_reviews, label_clusters
    from src.investigations import update_investigation_status
except ImportError:
    from reviews_data_processing_utils import process_datapoints, quantify_observations, generate_batches, add_uid_to_reviews, aggregate_all_categories, extractTagsForReview
    from firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, save_cluster_info_to_firestore, write_insights_to_firestore
    from openai_utils import get_completion_list_multifunction
    from reviews_clustering import cluster_reviews, label_clusters
    from investigations import update_investigation_status

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


# %%
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
# %%

# Define functions for data extraction
marketUserAnalysisReviewFunctions = [
    {
        "name": "marketUserAnalysis",
        "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
        "parameters": {
            "type": "object",
            "properties": {
                "useCase": {
                    "description": "Identifies the specific use case.",
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
                    "description": "Compare the product to competitors.",
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
                    "description": "Identifies the requested features or enhancements.",
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
                    "description": "Identifies the  patterns of usage frequency discussed.",
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
                    "description": "Identifies the different demographic segments.",
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

functionalEmotionalAnalysisReviewFunctions = [
    {
        "name": "functionalEmotionalAnalysis",
        "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
        "parameters": {
            "type": "object",
            "properties": {
                "functionalJob": {
                    "description": "Identifies main tasks or problems the product solves.",
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
                    "description": "Identifies how users want to be seen by others using the product.",
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
                    "description": "Identifies the tasks or activities that aid the main function of the product.",
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
                    "description": "Identifies the different pain points, specific challenges or problems customers encountered.",
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
GPT_MODEL = 'gpt-3.5-turbo-16k'

async def main():
    # List of function sets
    functionsList = [
        marketUserAnalysisReviewFunctions,
        functionalEmotionalAnalysisReviewFunctions
    ]
    
    # List of function calls
    functionsCallList = [
        {"name": "marketUserAnalysis"},
        {"name": "functionalEmotionalAnalysis"}
    ]
    
    responses = await get_completion_list_multifunction(contentList, functionsList, functionsCallList, GPT_MODEL=GPT_MODEL)
    return responses

responses = asyncio.run(main())


# %%
evalResponses = []

functionsCallList = [
        {"name": "marketUserAnalysis"},
        {"name": "functionalEmotionalAnalysis"} ]

response_index = 0
try:
    for batch in reviewBatches:
        for function in functionsCallList:
            item = responses[response_index]
            # Extracting the data from the response item
            data = item['function_call']['arguments']
            evalData = json.loads(data)
            evalResponses.append(evalData)
            response_index += 1
except Exception as e:
    logging.error(f"Error processing response item at index {response_index}: {e}")
    logging.error(f"Data causing the error: {data}")

# %%
try:
    aggregatedResponses = aggregate_all_categories(evalResponses)
except Exception as e:
    logging.error(f"Error in aggregating responses: {e}")
    aggregatedResponses = {}

# %%

# Updating the reviewsList to include tags
try:
    for reviewDict in updatedReviewsList:
        reviewUid = reviewDict['uid']
        tagsForReview = {}
        for evalData in aggregatedResponses:
            tags = extractTagsForReview(reviewUid, evalData)
            tagsForReview.update(tags)
        if tagsForReview:
            reviewDict['tags'] = tagsForReview
except Exception as e:
    logging.error(f"Error updating review list with tags for UID {reviewUid}: {e}")

# %%