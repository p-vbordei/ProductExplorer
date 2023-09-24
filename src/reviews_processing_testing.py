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
import os

try:
    from src import app
    from src.reviews_data_processing_utils import generate_batches, add_uid_to_reviews, aggregate_all_categories, quantify_category_data
    from src.firebase_utils import initialize_firestore, get_clean_reviews 
    from src.openai_utils import chat_completion_request, get_completion_list, get_completion_list_multifunction
    from src.investigations import update_investigation_status
except ImportError:
    from reviews_data_processing_utils import generate_batches, add_uid_to_reviews, aggregate_all_categories, quantify_category_data
    from firebase_utils import initialize_firestore, get_clean_reviews 
    from openai_utils import chat_completion_request, get_completion_list, get_completion_list_multifunction
    from investigations import update_investigation_status

# %%


investigationId = "KtTqXCON7AfZHNLOo4Df"

db = initialize_firestore()
if not db:
    logging.error("Error initializing Firestore.")


if not update_investigation_status(investigationId, 'startedReviews', db):
    logging.error(f"Error updating investigation status to 'startedReviews'.")


reviewsList = get_clean_reviews(investigationId, db)
print('Processing ', len(reviewsList), ' reviews')
if not reviewsList:
    logging.error("Error getting clean reviews.")


# Allocate short Ids to reviews
updatedReviewsList, uid_to_id_mapping = add_uid_to_reviews(reviewsList)

# Prepare Review Batches
reviewBatches = generate_batches(updatedReviewsList, max_tokens=6000)


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
# %%
# DECLARE FUNCTIONS 
marketFunctions = [
            {
                "name": "market",
                "description": "Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids.",
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
                                            }
                }
            }
        ]

extractJobsFunctions = [
            {
                "name": "extractJobs",
                "description": "Naming follows the JTBD framework. Group reviews on job statements for each type of job. Extract associated review ids. Job statement structure = verb + object of the verb (noun) + contextual clarifier",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "functionalJob": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "JobStatement": {
                                        "type": "string",
                                        "description": "",
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
                            "type": "array",
                            "items": {      
                                "type": "object",
                                "properties": {
                                    "JobStatement": {
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
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "JobStatement": {
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
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "JobStatement": {
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
                        "desiredOutcomes": {
                                "type": "object",
                                "properties": {
                                    "outcomeStatement": {
                                        "type": "string",
                                    }
                                }
                        },
                    }
                }
                
    }
]
# %%
extractJobsFunctionsV2 = [
    {
        "name": "extractJobs",
        "description": "Naming follows the JTBD framework. Group reviews on job statements for each type of job. Extract associated review ids. ",
        "parameters": {
            "type": "object",
            "properties": {
                "jobType": {
                    "type": "array",
                    "description": "An array of jobs of these types [functionalJob, socialJob, emotionalJob, supportingJob]",
                    "items": {
                        "type": "object",
                        "properties": {
                            "jobCategory": {
                                "type": "string",
                                "description": "The category of the job, e.g., functionalJob, socialJob, etc."
                            },
                            "jobs": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "jobStatement": {
                                            "type": "string",
                                            "description": "Job statement structure = verb + object of the verb (noun) + contextual clarifier"
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
            }
        }
    }
]


# %%
# Run GPT Calls for the Market function on the batches

#functionsList = [marketFunctions, extractJobsFunctions]
#functionsCallList = [{"name": "market"}, {"name": "extractJobs"}]
functionsList = [extractJobsFunctionsV2]
functionsCallList = [{"name": "extractJobs"}]
GPT_MODEL = 'gpt-3.5-turbo-16k'

# Get responses from GPT
async def main():
    responses = await get_completion_list_multifunction(contentList, functions_list=functionsList, function_calls_list=functionsCallList, GPT_MODEL=GPT_MODEL)
    return responses

responses = asyncio.run(main())
#################################################
# %%
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

# %%
# GPT that will cluster into distinct tags the tags from aggregatedResponses and place uids where they are the same

GPT_MODEL = 'gpt-3.5-turbo-16k'

messages = [
    {"role": "user", "content": f"Process the results from a function runing on multiple reviews batches. Group together uid's from simmilar labels. Keep only what is distinct. Take a deep breath and work on this problem step-by-step. \n {aggregatedResponses}."}
]

# Send the request to the LLM and get the response
response =  chat_completion_request(
    messages=messages,
    functions=marketFunctions,
    function_call={"name": "market"},
    temperature=0.3,
    model=GPT_MODEL
)
# %%
# Process the response and store in the dictionary
singleResponse = response.json()["choices"]

##################
# %%


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



# %%

tagedReviews = updatedReviewsList.copy()

for review in tagedReviews:
    # Get uid from the review
    uid = review.get('uid')
    # Fetch tags for the given uid from sortedResults
    tags = sortedResult.get(uid, {})
    # Add tags to the review
    review['tags'] = tags


# %%

# get the asin and review text for each uid
uid_to_asin = {review['uid']: review['asin'] for review in tagedReviews}
uid_to_text = {review['uid']: review['text'] for review in tagedReviews}
uid_to_rating = {review['uid']: review['rating'] for review in tagedReviews}

# Add asin to each uid
for key, value_list in processedData.items():
    for item in value_list:
        item['asin'] = [uid_to_asin[uid] for uid in item['uid']]


# %%

# Add rating to each uid
for key, value_list in processedData.items():
    for item in value_list:
        item['rating'] = [int(uid_to_rating[uid]) for uid in item['uid']]

# %%
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
                    'number': labelObservations,
                    'percentage': formattedLabelPercentage,
                    'rating': formattedAverageRating
                }
                
                processedLabels.append(processedLabelData)
            else:
                # Skip if no ratings
                continue
        
        processedData[categoryKey] = processedLabels
    
    return processedData

# %%

quantifiedData = quantify_category_data(processedData)


# %%
# Add the text from the reviews to each label
uid_to_text = {review['uid']: review['text'] for review in tagedReviews}

for key, value_list in quantifiedData.items():
    for item in value_list:
        item['customerVoice'] = [uid_to_text[uid] for uid in ite≠m['uid']]


# Add id to each uid
quantifiedDataId = quantifiedData.copy()
for key, value_list in quantifiedDataId.items():
    for item in value_list:
        item['id'] = [uid_to_id_mapping[uid] for uid in item['uid']]

# %%
