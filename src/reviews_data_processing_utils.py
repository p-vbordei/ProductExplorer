##########################
# data_processing_utils.py

import re
from tiktoken import get_encoding
import logging
logging.basicConfig(level=logging.INFO)
import numpy as np
import pandas as pd
import tiktoken

def num_tokens_from_string(string: str, encoding_name="cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    try:
        encoding = get_encoding(encoding_name)
        return len(encoding.encode(string))
    except Exception as e:
        logging.error(f"Error counting tokens: {e}")
        return 0

def clean_review(review_body):
    try:
        return re.sub(r'[^a-zA-Z0-9\s]+', '', review_body)
    except TypeError as e:
        logging.error(f"Error cleaning review: {e}")
        return ""

def initial_review_clean_data(df, limit=3000):
    try:
        df.loc[:, 'review'] = df['review'].apply(clean_review)
        df.loc[:, 'num_tokens'] = df['review'].apply(num_tokens_from_string)
        df.loc[:, 'review'] = df.apply(lambda x: x['review'][:limit * 3] if x['num_tokens'] > limit else x['review'], axis=1)
        df.loc[:, 'review_num_tokens'] = df['review'].apply(num_tokens_from_string)
        return df
    except Exception as e:
        logging.error(f"Error in initial_review_clean_data: {e}")
        return df

def initial_review_clean_data_list(reviews_list, limit=3000):
    try:
        for review_dict in reviews_list:
            review_dict['review'] = clean_review(review_dict['review'])
            review_dict['num_tokens'] = num_tokens_from_string(review_dict['review'])
            if review_dict['num_tokens'] > limit:
                review_dict['review'] = review_dict['review'][:limit * 3]
            review_dict['review_num_tokens'] = num_tokens_from_string(review_dict['review'])
        return reviews_list
    except Exception as e:
        logging.error(f"Error in initial_review_clean_data_list: {e}")
        return reviews_list

def process_datapoints(df):
    datapoints_list = []
    try:
        total = round(df['observationCount'].sum(), 0)

        for index, row in df.iterrows():
            data = {
                "attribute": row["attribute"],
                "clusterLabel": row["clusterLabel"],
                "observationCount": row['observationCount'],   # Count of Observations of Attribute Value
                "totalNumberOfObservations": total,  # Count of Observations of Attribute
                "percentageOfObservationsVsTotalNumberPerAttribute": round(row['percentageOfObservationsVsTotalNumberPerAttribute'], 2),
                "percentageOfObservationsVsTotalNumberOfReviews": round(row['percentageOfObservationsVsTotalNumberOfReviews'], 2)
            }
            datapoints_list.append(data)
        return datapoints_list
    except Exception as e:
        logging.error(f"Error in process_datapoints: {e}")
        return datapoints_list


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
    Adds a 'uid' to each review in the reviewsList based on its index and 
    returns a dictionary mapping from 'uid' to 'id'.

    Args:
    - reviewsList (list): List of dictionaries with reviews.

    Returns:
    - tuple: A tuple containing:
        - list: Updated list of reviews with 'uid' added.
        - dict: Dictionary mapping from 'uid' to 'id'.
    """

    # Extract 'id' from each dictionary
    ids = [review['id'] for review in reviewsList]

    # Create DataFrame
    id_uid_df = pd.DataFrame(ids, columns=['id'])
    id_uid_df['uid'] = id_uid_df.index

    # Create a mapping of 'id' to 'uid'
    id_to_uid_mapping = id_uid_df.set_index('id')['uid'].to_dict()

    # Initialize dictionary for 'uid' to 'id' mapping
    uid_to_id_mapping = {}

    # Add 'uid' to each dictionary in reviewsList
    for review in reviewsList:
        review['uid'] = id_to_uid_mapping.get(review['id'], None)
        uid_to_id_mapping[review['uid']] = review['id']

    return reviewsList, uid_to_id_mapping



# SPLIT TO BATCHES OF 'x' tokens
def generate_batches(reviews, max_tokens):
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


def aggregate_all_categories(data):
    """
    Aggregate items from all products under the same broad groupings.

    Parameters:
    - data (list): List of dictionaries representing products/categories.

    Returns:
    - dict: Aggregated items under the broad groupings.
    """
    aggregated_results = {}
    try:
        for product in data:
            for category_name, items in product.items():
                if category_name not in aggregated_results:
                    aggregated_results[category_name] = []
                aggregated_results[category_name].extend(items)
    except Exception as e:
        logging.error(f"Error in aggregate_all_categories: {e}")
        return {}
    return aggregated_results





def quantify_category_data(inputData):
    processedData = {}
    
    for categoryKey, labels in inputData.items():
        categoryTotalObservations = sum([len(labelData['uid']) for labelData in labels])
        processedLabels = []
        
        for labelData in labels:
            labelObservations = len(labelData['uid'])
            
            # Check for zero total observations and calculate label percentage
            labelPercentage = (labelObservations / categoryTotalObservations) * 100 if categoryTotalObservations != 0 else 0
            formattedLabelPercentage = int("{:.0f}".format(labelPercentage))
            
            # Check for zero length and calculate average rating for label
            if len(labelData['rating']) != 0:
                averageRating = sum(labelData['rating']) / len(labelData['rating'])
                formattedAverageRating = float("{:.1f}".format(averageRating))
                
                processedLabelData = {
                    'label': labelData['label'],
                    'uid': labelData['uid'],
                    'asin': list(set(labelData['asin'])),
                    'numberOfObservations': labelObservations,
                    'percentage': formattedLabelPercentage,
                    'rating': formattedAverageRating
                }
                
                processedLabels.append(processedLabelData)
            else:
                # Skip if no ratings
                continue
        
        processedData[categoryKey] = processedLabels
    
    return processedData


# =====================



def export_functions_for_reviews():
    marketFunctions = [
                {
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "useCase": {
                                "description": "Identifies up to 10 (ten) main specific use cases",
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "headerOfCategory (7 words)": {
                                            "type": "string",
                                        },
                                        "uid": {
                                            "type": "array",
                                            "items": {
                                                "type": "number"
                                            },
                                            "description": "Strict. Only the uid of those reviews that are associated with this header."
                                        }
                                    }
                                }
                            },
                            "productComparison": {
                                "description": "Compare the product to competitors, up to 10 observations.",
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "headerOfCategory (7 words)": {
                                            "type": "string",
                                        },
                                        "uid": {
                                            "type": "array",
                                            "items": {
                                                "type": "number"
                                            },
                                            "description": "Strict. Only the uid of those reviews that are associated with this header."
                                        }
                                    }
                                }
                            },
                            "featureRequest": {
                                "description": "Identifies up to 10 (ten) main requested features or enhancements",
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "headerOfCategory (7 words)": {
                                            "type": "string",
                                        },
                                        "uid": {
                                            "type": "array",
                                            "items": {
                                                "type": "number"
                                            },
                                            "description": "Strict. Only the uid of those reviews that are associated with this header."
                                        }
                                    }
                                }
                            },
                            "painPoints": {
                                "description": "Identifies up to 10 (ten) main different pain points, specific challenges or problems customers encountered",
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "headerOfCategory (7 words)": {
                                            "type": "string",
                                        },
                                        "uid": {
                                            "type": "array",
                                            "items": {
                                                "type": "number"
                                            },
                                            "description": "Strict. Only the uid of those reviews that are associated with this header."
                                        }
                                    }
                                }
                            },
                            "usageFrequency": {
                                "description": "Identifies up to 5 (five) main patterns of usage frequency discussed",
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "headerOfCategory (7 words)": {
                                            "type": "string",
                                        },
                                        "uid": {
                                            "type": "array",
                                            "items": {
                                                "type": "number"
                                            },
                                            "description": "Strict. Only the uid of those reviews that are associated with this header."
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
                                        "headerOfCategory (7 words)": {
                                            "type": "string",
                                        },
                                        "uid": {
                                            "type": "array",
                                            "items": {
                                                "type": "number"
                                            },
                                            "description": "Strict. Only the uid of those reviews that are associated with this header."
                                        }
                                    }
                                }
                            },
                            "usageLocation": {
                                "description": "Identifies up to 10 (ten) main locations where the product is used",
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "headerOfCategory (7 words)": {
                                            "type": "string",
                                        },
                                        "uid": {
                                            "type": "array",
                                            "items": {
                                                "type": "number"
                                            },
                                            "description": "Strict. Only the uid of those reviews that are associated with this header."
                                        }
                                    }
                                }
                            },
                            "customerDemographics": {
                                "description": "Identifies up to 10 (ten) main different demographic segments",
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "headerOfCategory (7 words)": {
                                            "type": "string",
                                        },
                                        "uid": {
                                            "type": "array",
                                            "items": {
                                                "type": "number"
                                            },
                                            "description": "Strict. Only the uid of those reviews that are associated with this header."
                                        }
                                    }
                                }
                            },
                                                }
                    },
                    "name": "market",
                    "description": "First, take a deep breath and go step-by-step. Begin by setting up empty lists for each category of market insights: Use Cases, Product Comparison, Feature Request, Pain Points, Usage Frequency, Usage Time, Usage Location, and Customer Demographics. Then, collect all relevant data. As you sift through each data piece, determine which category it fits into. Take note of the main topic, known as the 'header,' and compile a list of Unique IDs (UIDs) that relate specifically to that header. Create a new item that includes this information and add it to the appropriate category list. Make sure to remove any duplicate UIDs for each item. After you've sorted all the data, check if the lists are too large. If they are, trim them down to a manageable size; for example, keep up to 10 main points for most categories and up to 5 for Usage Frequency. Finally, consolidate these streamlined lists into one comprehensive market insights list. ",
                }
            ]

    extractJobsFunctions = [
                {
                    "parameters": {
                        "type": "object",
                        "properties": {
                                    "functionalJob": {
                                        "description": "Identifies up to 10 (ten) main tasks or problems the product solves. Example:'Help develop fine motor skills and hand-eye coordination', 'uid': [11, 27]} ",
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "objectiveStatement": {
                                                    "type": "string",
                                                },
                                                "uid": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "number"
                                                    },
                                                    "description": "Strict. Only the uid of those reviews that are associated with this header."
                                                }
                                            }
                                        }
                                    },
                                    "socialJob": {
                                        "description": "Identifies how users want to be seen by others using the product, up to 10 main situations. Example: 'Provide a shared activity for siblings or friends', 'uid': [37, 97]",
                                        "type": "array",
                                        "items": {      
                                            "type": "object",
                                            "properties": {
                                                "objectiveStatement": {
                                                    "type": "string",
                                                },
                                                "uid": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "number"
                                                    },
                                                    "description": "Strict. Only the uid of those reviews that are associated with this header."
                                                }
                                            }
                                        }
                                    },
                                    "emotionalJob": {
                                        "description": "Identifies up to 10 (ten) main feelings or states users aim to achieve with the product. Example: 'Provide a sense of accomplishment and pride for children', 'uid': [37, 97]",
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "objectiveStatement": {
                                                    "type": "string",
                                                },
                                                "uid": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "number"
                                                    },
                                                    "description": "Strict. Only the uid of those reviews that are associated with this header."
                                                }
                                            }
                                        }
                                    },
                                    "supportingJob": {
                                        "description": "Identifies up to 10 (ten) main tasks or activities that aid the main function of the product. Example: 'Help children develop cognitive skills such as counting, color matching, and pattern recognition', 'uid': [3, 14, 102]",
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "objectiveStatement": {
                                                    "type": "string",
                                                },
                                                "uid": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "number"
                                                    },
                                                    "description": "Strict. Only the uid of those reviews that are associated with this header."
                                                }
                                            }
                                        }
                                    },
                        }
                    },
                    "name": "extractJobs",
                    "description": "Naming follows the JTBD framework. Take a deep breath and proceed step by step. First, create empty lists for the four types of jobs: Functional, Social, Emotional, and Supporting. Then gather all the data that relates to these jobs. As you go through each piece of data, figure out what kind of job it talks about and jot down its main goal, also known as the Objective Statement. Also, make a list of unique IDs, or UIDs, that are linked to that main goal. Once you have this information, compile it into a new 'job item' and add that to the list that matches its job type. Be sure to remove any duplicate UIDs within each job item. After you've done all this, double-check the size of the lists you've created. If any of them are too large, trim them down so they fit within a set limit. Finally, combine these refined lists into one final output list. Job statement structure = verb + object of the verb (noun) + contextual clarifier. ",
                    
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
                        "description": "Identifies up to 10 (ten) main specific use cases",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
                                "headerOfCategory (7 words)": {
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
                        "description": "Identifies up to 10 (ten) main requested features or enhancements",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
                        "description": "Identifies up to 10 (ten) main different pain points, specific challenges or problems customers encountered",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
                        "description": "Identifies up to 5 (five) main patterns of usage frequency discussed",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
                        "description": "Identifies up to 5 (five) cases when the product is used",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
                        "description": "Identifies up to 5 (five) main locations where the product is used",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
                        "description": "Identifies up to 5 (five) main different demographic segments",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
                        "description": "Identifies up to 20 (twenty) main tasks or problems the product solves",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "objectiveStatement": {
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
                        "description": "Identifies up to 10 (ten) main views on how users want to be seen by others using the product",
                        "type": "array",
                        "items": {      
                            "type": "object",
                            "properties": {
                                "objectiveStatement": {
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
                        "description": "Identifies up to 5 (five) main feelings or states users aim to achieve with the product",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "objectiveStatement": {
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
                        "description": "Identifies up to 10 main tasks or activities that aid the main function of the product",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "objectiveStatement": {
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




        ##################

    useCaseFunction = [
        {
            "name": "useCaseFunction",
            "description": "You are an expert industrial product researcher. Aggregate reviews into categories, each representing a job type. Summarize each category with a single-sentence header with 7-10 words (do taxonomy). Extract the unique IDs of reviews under each category. Word order in reviews is not important. Limit the number of observations to 10. If more than 10 observations are received, reclassify until only 10 remain. Approach step-by-step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "useCase": {
                        "description": "Identifies the specific use case. Take it step by step, take a deep breath and count twice.",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
            "description": "ou are an expert industrial product researcher. Aggregate reviews into categories, each representing a job type. Summarize each category with a single-sentence header with 7-10 words (do taxonomy). Extract the unique IDs of reviews under each category. Word order in reviews is not important. Limit the number of observations to 10. If more than 10 observations are received, reclassify until only 10 remain. Approach step-by-step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "productComparison": {
                        "description": "Compare the product to competitors. Take it step by step, take a deep breath and count twice.",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
            "description": "ou are an expert industrial product researcher. Aggregate reviews into categories, each representing a job type. Summarize each category with a single-sentence header with 7-10 words (do taxonomy). Extract the unique IDs of reviews under each category. Word order in reviews is not important. Limit the number of observations to 10. If more than 10 observations are received, reclassify until only 10 remain. Approach step-by-step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "featureRequest": {
                        "description": "Identifies up to 10 (ten) main requested features or enhancements. Take it step by step, take a deep breath and count twice.",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
            "description": "You are an expert industrial product researcher. Aggregate reviews into categories, each representing a job type. Summarize each category with a single-sentence header with 7-10 words (do taxonomy). Extract the unique IDs of reviews under each category. Word order in reviews is not important. Limit the number of observations to 10. If more than 10 observations are received, reclassify until only 10 remain. Approach step-by-step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "painPoints": {
                        "description": "Identifies up to 10 (ten) main different pain points, specific challenges or problems customers encountered. Take it step by step, take a deep breath and count twice.",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
            "description": "You are an expert industrial product researcher. Aggregate reviews into categories, each representing a job type. Summarize each category with a single-sentence header with 7-10 words (do taxonomy). Extract the unique IDs of reviews under each category. Word order in reviews is not important. Limit the number of observations to 10. If more than 10 observations are received, reclassify until only 10 remain. Approach step-by-step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "usageFrequency": {
                        "description": "Identifies  up to 10 (ten) main patterns of usage frequency discussed. Take it step by step, take a deep breath and count twice.",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
            "description": "You are an expert industrial product researcher. Aggregate reviews into categories, each representing a job type. Summarize each category with a single-sentence header with 7-10 words (do taxonomy). Extract the unique IDs of reviews under each category. Word order in reviews is not important. Limit the number of observations to 10. If more than 10 observations are received, reclassify until only 10 remain. Approach step-by-step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "usageTime": {
                        "description": "Identifies when the product is used. Up to 10 (ten) main situations. Take it step by step, take a deep breath and count twice.",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
            "description": "You are an expert industrial product researcher. Aggregate reviews into categories, each representing a job type. Summarize each category with a single-sentence header with 7-10 words (do taxonomy). Extract the unique IDs of reviews under each category. Word order in reviews is not important. Limit the number of observations to 10. If more than 10 observations are received, reclassify until only 10 remain. Approach step-by-step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "usageLocation": {
                        "description": "Identifies where the product is used. Up to 10 (ten) main situations. Take it step by step, take a deep breath and count twice.",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
            "description": "You are an expert industrial product researcher. Aggregate reviews into categories, each representing a job type. Summarize each category with a single-sentence header with 7-10 words (do taxonomy). Extract the unique IDs of reviews under each category. Word order in reviews is not important. Limit the number of observations to 10. If more than 10 observations are received, reclassify until only 10 remain. Approach step-by-step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customerDemographics": {
                        "description": "Identifies the different demographic segments. Up to 10 categories. Take it step by step, take a deep breath and count twice.",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "headerOfCategory (7 words)": {
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
            "description": "You are an expert industrial product researcher. Aggregate reviews into categories, each representing a job type. Summarize each category with a single-sentence header with 7-10 words (do taxonomy). Extract the unique IDs of reviews under each category. Word order in reviews is not important. Limit the number of observations to 20. If more than 20 observations are received, reclassify until only 30 remain. Approach step-by-step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "functionalJob": {
                        "description": "Identifies up to twenty main tasks or problems the product solves. Up to 20 categories. Take it step by step, take a deep breath and count twice.",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "objectiveStatement": {
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
            "description": "You are an expert industrial product researcher. Aggregate reviews into categories, each representing a job type. Summarize each category with a single-sentence header with 7-10 words (do taxonomy). Extract the unique IDs of reviews under each category. Word order in reviews is not important. Limit the number of observations to 10. If more than 10 observations are received, reclassify until only 10 remain. Approach step-by-step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "socialJob": {
                        "description": "Identifies up to 20 (twenty) main tasks or problems the product solves. Take it step by step, take a deep breath and count twice.",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "objectiveStatement": {
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
            "description":"You are an expert industrial product researcher. Aggregate reviews into categories, each representing a job type. Summarize each category with a single-sentence header with 7-10 words (do taxonomy). Extract the unique IDs of reviews under each category. Word order in reviews is not important. Limit the number of observations to 10. If more than 10 observations are received, reclassify until only 10 remain. Approach step-by-step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emotionalJob": {
                        "description": "Identifies up to 10 (ten) feelings or states users aim to achieve with the product. Take it step by step, take a deep breath and count twice.",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "objectiveStatement": {
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
            "description": "You are an expert industrial product researcher. Aggregate reviews into categories, each representing a job type. Summarize each category with a single-sentence header with 7-10 words (do taxonomy). Extract the unique IDs of reviews under each category. Word order in reviews is not important. Limit the number of observations to 10. If more than 10 observations are received, reclassify until only 10 remain. Approach step-by-step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "supportingJob": {
                        "description": "Groups down and identify up to 10 main tasks or activities that aid the main function of the product. Take it step by step, take a deep breath and count twice.",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "objectiveStatement": {
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
    # Enumerate all funcitons
    return marketFunctions,  extractJobsFunctions, marketResponseHealFunction, useCaseFunction, productComparisonFunction, featureRequestFunction, painPointsFunction, usageFrequencyFunction, usageTimeFunction, usageLocationFunction, customerDemographicsFunction, functionalJobFunction, socialJobFunction, emotionalJobFunction, supportingJobFunction

