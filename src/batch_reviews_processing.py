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
    from src.openai_utils import get_completion_list
    from src.reviews_clustering import cluster_reviews, label_clusters
    from src.investigations import update_investigation_status
except ImportError:
    from reviews_data_processing_utils import process_datapoints, quantify_observations
    from firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, save_cluster_info_to_firestore, write_insights_to_firestore
    from openai_utils import get_completion_list
    from reviews_clustering import cluster_reviews, label_clusters
    from investigations import update_investigation_status

# %%
####################################### PROCESS REVIEWS WITH GPT #######################################


def process_reviews_with_gpt(reviewsList, db):
    try:
        # Start the timer
        start_time = time.time()

    # Define review functions
        reviewFunctions = [
            {
                "name": "reviewDataFunction",
                "description": "retreive information from reviews",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reviewSummary": {
                            "type": "string",
                            "description": "A brief summary of the review. Eg: Good product overall, but improvements can be made in battery life and noise levels."
                        },
                        "buyerMotivation": {
                            "type": "string",
                            "description": "Reasons why the buyer purchased the product. Eg: to replace an old product, to try out a new product, to give as a gift"
                        },
                        "customerExpectations": {
                            "type": "string",
                            "description": "Expectations the customer had before purchasing the product. Eg: to be able to use the product for a long time, to be able to use the product in a variety of situations, to be able to use the product for a specific purpose"
                        },
                        "howTheProductIsUsed": {
                            "type": "string",
                            "description": "Information about what the product is used for or about how the product is used. Eg: doodling, practicing letters/shapes, playing games"
                        },
                        "whereTheProductIsUsed": {
                            "type": "string",
                            "description": "Suggested locations or situations where the product can be used. Eg: car, restaurant, garden, public parks"
                        },
                        "userDescription": {
                            "type": "string",
                            "description": "Description of the user for the product. Eg: children, preschoolers, basketball players, mothers, office workers"
                        },
                        "packaging": {
                            "type": "string",
                            "description": "Description of the product's packaging. Eg: sturdy recyclable box, wrapped in plastic, great for gifting"
                        },
                        "season": {
                            "type": "string",
                            "description": "Eg: fall and winter"
                        },
                        "whenTheProductIsUsed": {
                            "type": "string",
                            "description": "Time of day or week of use. Eg: early in the morning"
                        },
                        "appraisal": {
                            "type": "string",
                            "description": "observations on price or value"
                        },
                        "quality": {
                            "type": "string",
                            "description": "Observations on the quality. Eg: poor quality, great quality"
                        },
                        "durability": {
                            "type": "string",
                            "description": "Observations on the durability. Eg: not durable, durable, very durable"
                        },
                        "easeOfUse": {
                            "type": "string",
                            "description": "Observations on the ease of use. Eg: not easy to use, easy to use"
                        },
                        "setupAndInstructions": {
                            "type": "string",
                            "description": "Observations on the setup. Eg: not easy to set up, easy to set up, easy to follow instructions, not clear instructions"
                        },
                        "noiseAndSmell": {
                            "type": "string",
                            "description": "Observations on the noise level or smell. Eg: too loud, quiet, squeaky, smells like roses, plastic smell"
                        },
                        "sizeAndFit": {
                            "type": "string",
                            "description": "Observations on the fit. Eg: too tight, too loose, fits well, too small, too big"
                        },
                        "dangerAppraisal": {
                            "type": "string",
                            "description": "Observations on the safety of the product. Eg: dangerous, hazardous, safe, can break and harm, safe for children"
                        },
                        "designAndAppearance": {
                            "type": "string",
                            "description": "Observations on the design and appearance. Eg: not attractive, attractive, love the design, love the appearance"
                        },
                        "partsAndComponents": {
                            "type": "string",
                            "description": "Observations on the parts and components. Eg: missing parts, all parts included, parts are easy to assemble"
                        },
                        "issues": {
                            "type": "string",
                            "description": "If specified. Actionable observations on product problems to be addressed. Thorough detailing [max 100 words]. Eg: the product started to rust after one year, although I was expecting it to last 5 years before rusting."
                        },
                    },
                    "required": ["reviewSummary", "buyerMotivation", "customerExpectations", "howTheProductIsUsed", "whereTheProductIsUsed", "appraisal","userDescription", "packaging", "season", "whenTheProductIsUsed", "price", "quality", "durability", "easeOfUse", "setupAndInstructions", "noiseAndSmell", "colors", "sizeAndFit", "dangerAppraisal", "designAndAppearance", "partsAndComponents", "issues"]
                },
            }
        ]





        functions = reviewFunctions
        function_call = {"name": "reviewDataFunction"}

        contentList = []
        for reviewDict in reviewsList:
            try:
                review = reviewDict['text']
            except KeyError:
                logging.error(f"KeyError: 'text' not found in dictionary at index {i}. Full dict: {reviewDict}")
                continue
            messages = [
                {"role": "user", "content": f"REVIEW: ```{review}```"},
            ]
            contentList.append(messages)
        logging.info("Content list prepared.")

        async def main():
            responses = await get_completion_list(contentList, functions, function_call)
            return responses

        responses = asyncio.run(main())

        evalResponses = []
        for i, item in tqdm(enumerate(responses), total=len(responses), desc="Processing reviews"):
            data = item['function_call']['arguments']
            data = data.replace('null', 'None')
            evalData = eval(data)
            evalResponses.append(evalData)
            reviewsList[i]['insights'] = evalData
            logging.debug(f"Processed response {i+1}/{len(responses)}.")

        newCols = list(reviewsList[1]['insights'].keys())

        for i, reviewDict in tqdm(enumerate(reviewsList), total=len(reviewsList), desc="Updating review dictionaries"):
            for col in newCols:
                try:
                    reviewDict[col] = reviewDict['insights'][col]
                except KeyError as e:
                    logging.warning(f"KeyError: {e}")
                    reviewDict[col] = None
            reviewDict.pop('insights')
            logging.debug(f"Updated review dictionary {i+1}/{len(reviewsList)}.")

        write_reviews_to_firestore(reviewsList, db)

        # Stop the timer and print the elapsed time
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"Total time taken for processing: {elapsed_time:.2f} seconds")

        return reviewsList

    except Exception as e:
        logging.error(f"Error in process_reviews_with_gpt: {e}")
        return None  # Return None in case of error

############################################ RUN ############################################

# %%


def run_reviews_investigation(investigationId):
    try:
        # Initialize Firestore
        db = initialize_firestore()
        logging.info("Initialized Firestore successfully.")
    except Exception as e:
        logging.error(f"Error initializing Firestore: {e}")
        return
    
    try:
        update_investigation_status(investigationId, 'startedReviews', db)
    except Exception as e:
        logging.error(f"Error updating investigation status to 'startedReviews': {e}")
        pass

    try:
        # Get clean reviews
        reviews = get_clean_reviews(investigationId, db)
        logging.info("Retrieved clean reviews successfully.")
    except Exception as e:
        logging.error(f"Error getting clean reviews: {e}")
        return

    try:
        # Process reviews with GPT
        cleanReviews = process_reviews_with_gpt(reviews, db)
        logging.info("Processed reviews with GPT successfully.")
    except Exception as e:
        logging.error(f"Error processing reviews with GPT: {e}")
        return
    
    try:
        update_investigation_status(investigationId, 'finishedProcessingReviewsWithGPT', db)
    except Exception as e:
        logging.error(f"Error updating investigation status to 'finishedProcessingReviewsWithGPT': {e}")
        pass

    try:
        # Cluster reviews
        cluster_df = cluster_reviews(cleanReviews)
        logging.info("Clustered reviews successfully.")
    except Exception as e:
        logging.error(f"Error clustering reviews: {e}")
        return

    try:
        # Label clusters
        reviewsWithClusters = label_clusters(cluster_df)
        logging.info("Labeled clusters successfully.")
    except Exception as e:
        logging.error(f"Error labeling clusters: {e}")
        return

    try:
        # Quantify observations
        attributeClustersWithPercentage, attributeClustersWithPercentageByAsin = quantify_observations(reviewsWithClusters, cleanReviews)
        logging.info("Quantified observations successfully.")
    except Exception as e:
        logging.error(f"Error quantifying observations: {e}")
        return

    try:
        # Save results to Firestore
        save_cluster_info_to_firestore(attributeClustersWithPercentage, attributeClustersWithPercentageByAsin, investigationId, db)
        logging.info("Saved cluster info to Firestore successfully.")
    except Exception as e:
        logging.error(f"Error saving cluster info to Firestore: {e}")
        return

    try:
        # Process datapoints
        datapoints = list(set(attributeClustersWithPercentage['attribute']))
        datapointsDict = {}
        for att in datapoints:
            df = attributeClustersWithPercentage[attributeClustersWithPercentage['attribute'] == att]
            datapoints_list = process_datapoints(df)
            datapointsDict[att] = datapoints_list
        logging.info("Processed datapoints successfully.")
    except Exception as e:
        logging.error(f"Error processing datapoints: {e}")
        return

    try:
        # Write insights to Firestore
        write_insights_to_firestore(investigationId, datapointsDict, db)
        logging.info("Wrote insights to Firestore successfully.")
    except Exception as e:
        logging.error(f"Error writing insights to Firestore: {e}")
        return
    
    try:
        update_investigation_status(investigationId, 'finishedReviews', db)
    except Exception as e:
        logging.error(f"Error updating investigation status to 'finishedReviews': {e}")
        pass
    
    logging.info(f"Reviews investigation for {investigationId} completed successfully.")

# ====================



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
    reviews = get_clean_reviews(investigationId, db)
    logging.info("Retrieved clean reviews successfully.")
except Exception as e:
    logging.error(f"Error getting clean reviews: {e}")

# %%

reviewFunctions = [
    {
        "name": "reviewsTagsFunction",
        "description": "tag reviews with attributes",
        "parameters": {
            "type": "object",
            "properties": {
                "buyerMotivationReviews": {
                    "description": "Reasons why the buyer purchased the product. Eg: to replace an old product, to try out a new product, to give as a gift",
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "list",
                            "description": "id of reviews"
                        },
                        "buyerMotivation": {
                            "type": "string",
                            "description": "review snippets with buyer motivation"
                        }
                    }
                }
            },
        "required": ["buyerMotivationReviews"]
        },
    }
]
                






functions = reviewFunctions
function_call = {"name": "reviewsTagsFunction"}

contentList = []
for reviewDict in reviewsList:
    try:
        review = reviewDict['text']
    except KeyError:
        logging.error(f"KeyError: 'text' not found in dictionary at index {i}. Full dict: {reviewDict}")
        continue
    messages = [
        {"role": "user", "content": f"REVIEW: ```{review}```"},
    ]
    contentList.append(messages)
logging.info("Content list prepared.")

async def main():
    responses = await get_completion_list(contentList, functions, function_call)
    return responses

responses = asyncio.run(main())

evalResponses = []
for i, item in tqdm(enumerate(responses), total=len(responses), desc="Processing reviews"):
    data = item['function_call']['arguments']
    data = data.replace('null', 'None')
    evalData = eval(data)
    evalResponses.append(evalData)
    reviewsList[i]['insights'] = evalData
    logging.debug(f"Processed response {i+1}/{len(responses)}.")

newCols = list(reviewsList[1]['insights'].keys())

for i, reviewDict in tqdm(enumerate(reviewsList), total=len(reviewsList), desc="Updating review dictionaries"):
    for col in newCols:
        try:
            reviewDict[col] = reviewDict['insights'][col]
        except KeyError as e:
            logging.warning(f"KeyError: {e}")
            reviewDict[col] = None
    reviewDict.pop('insights')
    logging.debug(f"Updated review dictionary {i+1}/{len(reviewsList)}.")


#######################
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

functions = marketUserAnalysisReviewFunctions
function_call = {"name": "marketUserAnalysis"}


# %%
functions =  functionalEmotionalAnalysisReviewFunctions
function_call = {"name": "functionalEmotionalAnalysis"}

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
    responses = await get_completion_list(contentList, functions, function_call, GPT_MODEL=GPT_MODEL)
    return responses

responses = asyncio.run(main())




# %%
evalResponses = []
idx = 0  # to track the global index in reviewsList
for batch, item in tqdm(zip(review_batches, responses), total=len(responses), desc="Processing reviews batches"):
    data = item['function_call']['arguments']
    data = data.replace('null', 'None')
    evalData = eval(data)
    evalResponses.append(evalData)

    # Distribute insights from batch response to individual reviews
    for (review_id, review_text) in batch:
        corresponding_review = next(r for r in reviewsList if r['id'] == review_id)
        corresponding_review['insights'] = evalData  # Update as per your processing needs
        idx += 1
# %%
# Updating Review Dictionaries
newCols = list(reviewsList[1]['insights'].keys())
for i, reviewDict in tqdm(enumerate(reviewsList), total=len(reviewsList), desc="Updating review dictionaries"):
    for col in newCols:
        try:
            reviewDict[col] = reviewDict['insights'][col]
        except KeyError as e:
            logging.warning(f"KeyError: {e}")
            reviewDict[col] = None
    reviewDict.pop('insights')
    logging.debug(f"Updated review dictionary {i+1}/{len(reviewsList)}.")
# %%



#####
# RAMAS DE FACUT\
# PARTEA DE JOS E BATCH PROCESSING
# ASTA E DE TERMINAT
# REVIEW IDs trebuie schimbate in ceva muult mai skinny, niste numere
# %%
# Trebuie scoase spatiile goale din schema de functie
# Trebuie facut batch processing pentru ambele functii, adica schimbata functia de completion pt a accepta 2 functii atunci cand scrie procesul de batching asinc
# Trebuie rescrisa intreaga arhitectura de procesare rezultate