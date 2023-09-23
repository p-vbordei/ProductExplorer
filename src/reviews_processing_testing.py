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
#########################

extractJobsFunctions = [
            {
                "name": "extractJobs",
                "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job. Extract associated review ids. "
                "parameters": {
                    "type": "object",
                    "properties": {
                        "functionalJob": {
                            "description": "Identifies main tasks or problems the product solves. ",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "JobStatement": {
                                        "type": "string",
                                        "description: A job statement is a concise sentence that outlines what a user aims to achieve with the product. It starts with a verb, followed by the object of that verb, which is usually a noun. Additionally, the statement includes a contextual clarifier to specify the conditions or situations in which the job is performed. For example, 'listen to music while on the go' is a job statement where 'listen to music' is the core job and 'while on the go' is the contextual clarifier. Another example is 'get breakfast while commuting to work,' where 'get breakfast' is the job and 'while commuting to work' provides the context. Always adhere to this format for consistency."
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
                            "description": "Identifies the feelings or states users aim to achieve with the product",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "JobStatement": {
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
                        }    },
                        "desiredOutcomes": {
                            "description": "This category captures the specific improvements that users desire when using the product. Each desired outcome is a statement that combines four elements: a direction of improvement (e.g., minimize, maximize), a performance metric (usually time or likelihood), an object of control (what specifically should be improved), and a contextual clarifier (the situation in which the improvement is desired).",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "outcomeStatement": {
                                        "type": "string",
                                        "description": "This is a comprehensive statement that outlines what improvement is desired by the user. It combines a direction of improvement (like 'minimize' or 'maximize'), a performance metric (such as time taken or likelihood), the specific aspect that needs improvement (object of control), and the context in which this improvement is desired."
                                    },
                                    "JobStatements": {
                                        "type": "array",
                                        "items": { "type": "string" },
                                        "description": "This is a list of Functional Jobs that are directly related to the desired outcome. These Functional Jobs serve as the basis for understanding why the outcome is important and in what context. Each entry in this array should correspond to a Job Statement defined in the 'functionalJob' category."
                                    }
                                }
                            }
                        },
                    }
                }
            }
        ]
#########################




# %%
# Run GPT Calls for the Market function on the batches

# functionsList = [marketFunctions, extractJobsFunctions]
# functionsCallList = [{"name": "market"}, {"name": "extractJobs"}]

functionsList = [extractJobsFunctions]
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
