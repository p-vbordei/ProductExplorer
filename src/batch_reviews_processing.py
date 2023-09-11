# ##################
# reviews_processing.py
# %%
import asyncio
from tqdm import tqdm
import time
import logging
import pandas as pd
logging.basicConfig(level=logging.INFO)

try:
    from src import app
    from src.reviews_data_processing_utils import process_datapoints, quantify_observations
    from src.firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, save_cluster_info_to_firestore, write_insights_to_firestore
    from src.openai_utils import get_completion_list_multifunction
    from src.reviews_clustering import cluster_reviews, label_clusters
    from src.investigations import update_investigation_status
except ImportError:
    from reviews_data_processing_utils import process_datapoints, quantify_observations
    from firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, save_cluster_info_to_firestore, write_insights_to_firestore
    from openai_utils import get_completion_list_multifunction
    from reviews_clustering import cluster_reviews, label_clusters
    from investigations import update_investigation_status

# %%

import tiktoken

def transform_rating_to_star_format(rating):
    """
    Transforms a numerical or textual rating to a star format.

    Args:
    - rating (int or str): A numerical rating value between 1 to 5 or a textual rating.

    Returns:
    - str: A string representation of the rating in the format "5*" or "1*", or the textual rating followed by a "*".
    """
    
    if isinstance(rating, int) and 1 <= rating <= 5:
        return f"{rating}*"
    elif isinstance(rating, str):
        return f"{rating}*"
    else:
        raise ValueError("Rating must be a number between 1 and 5 or a textual value.")

def add_uid_to_reviews(reviewsList):
    """
    Adds a 'uid' to each review in the reviewsList based on its index.

    Args:
    - reviewsList (list): List of dictionaries with reviews.

    Returns:
    - list: Updated list of reviews with 'uid' added.
    """

    # Extract 'id' from each dictionary
    ids = [review['id'] for review in reviewsList]

    # Create DataFrame
    id_uid_df = pd.DataFrame(ids, columns=['id'])
    id_uid_df['uid'] = id_uid_df.index

    # Create a mapping of 'id' to 'uid'
    id_to_uid_mapping = id_uid_df.set_index('id')['uid'].to_dict()

    # Add 'uid' to each dictionary in reviewsList
    for review in reviewsList:
        review['uid'] = id_to_uid_mapping.get(review['id'], None)

    return reviewsList

def num_tokens_from_string(string: str, encoding_name = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


# SPLIT TO BATCHES OF 'x' tokens
def generate_batches(reviews, max_tokens=6000):
    """
    This function takes a list of reviews and groups them into batches based on token count. Each batch 
    has a token count that doesn't exceed the specified max_tokens limit. It returns a list of batches, 
    where each batch is a list of tuples. Each tuple contains a review ID and its corresponding text.
    
    Args:
        reviews (list of dicts): A list of review dictionaries. Each dictionary has keys 'id' and 'text'.
        max_tokens (int): The maximum number of tokens allowed per batch.

    Returns:
        batches (list): A list of lists, where each inner list represents a batch of tuples.
    """
    batches = []
    current_batch = []
    current_tokens = 0

    for review in reviews:
        review_id = review['uid']
        review_text = review['text']
        review_rating = transform_rating_to_star_format(review['rating'])

        imp_tokens = num_tokens_from_string(review_text, encoding_name="cl100k_base")
        if current_tokens + imp_tokens + 1 <= max_tokens:
            current_batch.append((review_id,review_rating, review_text))
            current_tokens += imp_tokens + 1
        else:
            batches.append(current_batch)
            current_batch = [(review_id, review_rating, review_text)]
            current_tokens = imp_tokens
    if current_batch:
        batches.append(current_batch)

    return batches


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
updated_reviewsList = add_uid_to_reviews(reviewsList)


# %%
# Prepare Review Batches
review_batches = generate_batches(updated_reviewsList, max_tokens=8000)

# %%
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
                            "id": {
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
                            "id": {
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
                            "id": {
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
                            "id": {
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
                            "id": {
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
                            "id": {
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
                            "id": {
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
                            "id": {
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
                            "id": {
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
                            "id": {
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

#functions = marketUserAnalysisReviewFunctions
#function_call = {"name": "marketUserAnalysis"}


# %%
#functions =  functionalEmotionalAnalysisReviewFunctions
#function_call = {"name": "functionalEmotionalAnalysis"}

# %%
# Generate Content List for Batches
contentList = []

for batch in review_batches:
    batch_review = f"\n\n <Review IDs>  will be followed by <Review Rating> and than by  `review text`:"
    batch_review += "\n\n".join([f"<{review_id}>\n,<{review_rating}>\n,`{review_text}`" for review_id, review_rating, review_text in batch])
    
    messages = [
        {"role": "user", "content": batch_review},
    ]
    contentList.append(messages)

logging.info("Content list prepared.")


# %%
GPT_MODEL = 'gpt-3.5-turbo-16k'

async def main():
    # List of function sets
    functions_list = [
        marketUserAnalysisReviewFunctions,
        functionalEmotionalAnalysisReviewFunctions
    ]
    
    # List of function calls
    function_calls_list = [
        {"name": "marketUserAnalysis"},
        {"name": "functionalEmotionalAnalysis"}
    ]
    
    responses = await get_completion_list_multifunction(contentList, functions_list, function_calls_list, GPT_MODEL=GPT_MODEL)
    return responses

responses = asyncio.run(main())

# %%

evalResponses = []

for batch, item in zip(review_batches, responses):
    try:
        # Extracting the data from the response item
        data = item['function_call']['arguments']
        data = data.replace('null', 'None')
        evalData = eval(data)
        evalResponses.append(evalData)
    except Exception as e:
        logging.error(f"Error processing response item: {e}")

# Function to extract tags for a review
def extractTagsForReview(reviewUid, evalData):
    tags = {}
    try:
        for topic, labels in evalData.items():
            for label in labels:
                if reviewUid in label['id']:
                    tags[topic] = tags.get(topic, [])
                    tags[topic].append(label['label'])
    except Exception as e:
        logging.error(f"Error extracting tags for review with UID {reviewUid}: {e}")
    return tags

# Updating the reviewsList to include tags
for reviewDict in reviewsList:
    try:
        reviewUid = reviewDict['uid']
        tagsForReview = {}
        for evalData in evalResponses:
            tags = extractTagsForReview(reviewUid, evalData)
            tagsForReview.update(tags)
        if tagsForReview:
            reviewDict['tags'] = tagsForReview
    except Exception as e:
        logging.error(f"Error processing review with UID {reviewUid}: {e}")


# %%