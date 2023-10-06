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
    from src.reviews_data_processing_utils import generate_batches, add_uid_to_reviews, aggregate_all_categories,  quantify_category_data
    from src.firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, write_insights_to_firestore
    from src.openai_utils import chat_completion_request, get_completion_list_multifunction
    from src.investigations import update_investigation_status
except ImportError:
    from reviews_data_processing_utils import generate_batches, add_uid_to_reviews, aggregate_all_categories,  quantify_category_data
    from firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, write_insights_to_firestore
    from openai_utils import chat_completion_request, get_completion_list_multifunction
    from investigations import update_investigation_status

# %%
investigationId = "40hlz64Ifn2pklb2A5P8"
userId = "XgneABVFF3MrwekpsjpHIlOhdnB3"

db = initialize_firestore()
if not db:
    logging.error("Error initializing Firestore.")


if not update_investigation_status(userId, investigationId, 'startedReviews', db):
    logging.error(f"Error updating investigation status to 'startedReviews'.")


reviews = get_clean_reviews(userId, investigationId, db)
print('Processing ', len(reviews), ' reviews')
if not reviews:
    logging.error("Error getting clean reviews.")

# %%
reviewsList = reviews.copy()

# %%
"""
Process reviews using GPT and extract insights.

Parameters:
- reviewsList (list): List of reviews to be processed.
- db: Firestore database instance.

Returns:
- list: Updated reviews list with extracted insights.
"""

# Allocate short Ids to reviews
updatedReviewsList, uid_to_id_mapping = add_uid_to_reviews(reviewsList)

# Prepare Review Batches
reviewBatches = generate_batches(updatedReviewsList, max_tokens=6000)

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
                "description": "Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids. Let's think step by step. Start by writing down all the different detailing sentences. After that, write down the uids where the detailing sentence is mentioned.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "useCase": {
                            "description": "Identifies the specific use case. ,",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "detailingSentence": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        },
                                        "description": "Strict. Only the uid of those reviews that are associated with this label."
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
                                    "detailingSentence": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        },
                                        "description": "Strict. Only the uid of those reviews that are associated with this label."
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
                                    "detailingSentence": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        },
                                        "description": "Strict. Only the uid of those reviews that are associated with this label."
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
                                    "detailingSentence": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        },
                                        "description": "Strict. Only the uid of those reviews that are associated with this label."
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
                                    "detailingSentence": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        },
                                        "description": "Strict. Only the uid of those reviews that are associated with this label."
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
                                    "detailingSentence": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        },
                                        "description": "Strict. Only the uid of those reviews that are associated with this label."
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
                                    "detailingSentence": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        },
                                        "description": "Strict. Only the uid of those reviews that are associated with this label."
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
                                    "detailingSentence": {
                                        "type": "string",
                                    },
                                    "uid": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        },
                                        "description": "Strict. Only the uid of those reviews that are associated with this label."
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
                "description": "Naming follows the JTBD framework. Group reviews on job statements for each type of job. Extract associated review ids. Job statement structure = verb + object of the verb (noun) + contextual clarifier. Let's think step by step. Start by writing down all the different objective (job) statements. After that, write down the uids where the jobs are mentioned.",
                "parameters": {
                    "type": "object",
                    "properties": {
                                "functionalJob": {
                                    "description": "Identifies main tasks or problems the product solves. Example:'Help develop fine motor skills and hand-eye coordination', 'uid': [11, 27]} ",
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
                                                "description": "Strict. Only the uid of those reviews that are associated with this label."
                                            }
                                        }
                                    }
                                },
                                "socialJob": {
                                    "description": "Identifies how users want to be seen by others using the product. Example: 'Provide a shared activity for siblings or friends', 'uid': [37, 97]",
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
                                                "description": "Strict. Only the uid of those reviews that are associated with this label."
                                            }
                                        }
                                    }
                                },
                                "emotionalJob": {
                                    "description": "Identifies the feelings or states users aim to achieve with the product. Example: 'Provide a sense of accomplishment and pride for children', 'uid': [37, 97]",
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
                                                "description": "Strict. Only the uid of those reviews that are associated with this label."
                                            }
                                        }
                                    }
                                },
                                "supportingJob": {
                                    "description": "Identifies the tasks or activities that aid the main function of the product. Example: 'Help children develop cognitive skills such as counting, color matching, and pattern recognition', 'uid': [3, 14, 102]",
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
                                                "description": "Strict. Only the uid of those reviews that are associated with this label."
                                            }
                                        }
                                    }
                                },
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
                                    "detailingSentence": {
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
                                    "detailingSentence": {
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
                                    "detailingSentence": {
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
                                    "detailingSentence": {
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
                                    "detailingSentence": {
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
                                    "detailingSentence": {
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
                                    "detailingSentence": {
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
                                    "detailingSentence": {
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
                            "description": "Identifies how users want to be seen by others using the product",
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
                            "description": "Identifies the feelings or states users aim to achieve with the product",
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
                            "description": "Identifies the tasks or activities that aid the main function of the product",
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

############

# %%


import aiohttp
import asyncio
import os
import numpy as np
import random
import pandas as pd
from tenacity import retry, wait_random_exponential, stop_after_attempt
import requests
import tiktoken
import nest_asyncio
nest_asyncio.apply()
import logging
logging.basicConfig(level=logging.INFO)
import traceback
from aiohttp import ContentTypeError, ClientResponseError

def get_openai_key():
    """Retrieve OpenAI API key."""

    # Try to get the key from environment variable
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # If not found, try to get from secret management
    if not OPENAI_API_KEY:
        try:
            from src.firebase_utils import get_secret
            OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
        except:
            pass

    # If still not found, load from .env (mostly for local development)
    if not OPENAI_API_KEY:
        from dotenv import load_dotenv
        load_dotenv()
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in environment or secrets")

    return OPENAI_API_KEY

OPENAI_API_KEY = get_openai_key()


HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}"
}

class ProgressLog:
    def __init__(self, total):
        self.total = total
        self.done = 0

    def increment(self):
        self.done = self.done + 1

    def __repr__(self):
        return f"Done runs {self.done}/{self.total}."
    
@retry(wait=wait_random_exponential(min=1, max=180), stop=stop_after_attempt(10), before_sleep=print, retry_error_callback=lambda retry_state: print(f"Attempt {retry_state.attempt_number} failed. Error: {retry_state.outcome.result()}"))
async def get_completion(content, session, semaphore, progress_log, functions=None, function_call=None, GPT_MODEL=GPT_MODEL):
    async with semaphore:
        await asyncio.sleep(5.45)  # Introduce a 5.45-second delay between requests. This is to avoid hitting the RPM & TPM limits.
        
        json_data = {
            "model": GPT_MODEL,
            "messages": content,
            "temperature": 0
        }
        
        if functions is not None:
            json_data.update({"functions": functions})
        if function_call is not None:
            json_data.update({"function_call": function_call})

        try:
            async with session.post("https://api.openai.com/v1/chat/completions", headers=HEADERS, json=json_data) as resp:
                resp.raise_for_status()  # This will raise an error for 4xx and 5xx responses
                
                try:
                    response_json = await resp.json()
                except ContentTypeError:
                    logging.error("Failed to decode API response as JSON.")
                    raise

                if "error" in response_json:
                    error_message = response_json["error"]["message"]
                    logging.error(f"OpenAI API Error: {error_message}")
                    raise ValueError(error_message)

                try:
                    print(response_json['usage'])
                except KeyError:
                    logging.warning("Usage data not found in the response.")
                
                print(response_json)
                progress_log.increment()
                print(progress_log)
                return response_json["choices"][0]['message']

        except ClientResponseError as e:
            logging.error(f"HTTP Error {e.status}: {e.message}")
            if e.status == 400:
                raise ValueError("Bad Request: The API request was malformed.")
            elif e.status == 401:
                raise PermissionError("Unauthorized: Check your API key.")
            elif e.status == 403:
                raise PermissionError("Forbidden: You might have exceeded your rate limits or don't have permission.")
            elif e.status == 404:
                raise ValueError("Endpoint not found.")
            elif e.status in [429, 502, 503, 504]:
                logging.warning("Temporary API issue or rate limit hit. Retrying...")
            else:
                raise
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            traceback.print_exc()
            raise

# %%


async def get_completion_list_multifunction(content_list, functions_list, function_calls_list, GPT_MODEL=GPT_MODEL):
    semaphore = asyncio.Semaphore(6)
    progress_log = ProgressLog(len(content_list) * len(functions_list))

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
        tasks = []
        for i in range(len(functions_list)):
            for content in content_list:
                tasks.append(get_completion(content, session, semaphore, progress_log, functions_list[i], function_calls_list[i], GPT_MODEL))
        return await asyncio.gather(*tasks)




#########

# %%
# Run GPT Calls for the Market function on the batches

functionsList = [marketFunctions, extractJobsFunctions]
functionsCallList = [{"name": "market"}, {"name": "extractJobs"}]
GPT_MODEL = 'gpt-3.5-turbo-16k'

# Get responses from GPT
async def main():
    responses = await get_completion_list_multifunction(contentList, functions_list=functionsList, function_calls_list=functionsCallList, GPT_MODEL=GPT_MODEL)
    return responses

responses = asyncio.run(main())


# %%
# Process the responses
evalResponses = []
# Iterage through responses
for index in range(len(responses)):
    print(index)
    item = responses[index]
    data = item['function_call']['arguments']
    # Try to parse the response data
    try:
        evalData = json.loads(data)
        evalResponses.append(evalData)
    except:
        print(f"Error processing response for batch {index}.")
        pass

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
                            "detailingSentence": {
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
                            "detailingSentence": {
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
                            "detailingSentence": {
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
                            "detailingSentence": {
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
                            "detailingSentence": {
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
                            "detailingSentence": {
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
                            "detailingSentence": {
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
                            "detailingSentence": {
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

functionsResponses = []
for key, function in functionMapping.items():
    if key in aggregatedResponses:
        contentList = [
            {"role": "user", "content": f"Process the results for key: {key}. Group together uid's from similar labels. Keep only what is distinct. Take a deep breath and work on this problem step-by-step. Limit the number of UIds if you need to in order to reach the token limit with no errors.\n {aggregatedResponses[key]}"}
        ]
        print({"name": function[0]["name"]})
        response = chat_completion_request(contentList, function, {"name": function[0]["name"]} ,temperature=0.5,model=GPT_MODEL)
        functionsResponses.append(response)
    else:
        pass




# %%
# Processes Results
processedResults = []
for idx, response in enumerate(functionsResponses):
    key = list(aggregatedResponses.keys())[idx]
    resp = response.json()['choices']
    data = resp[0]['message']['function_call']['arguments']
    try:
        evalData = json.loads(data)
    except:
        healingResponse = chat_completion_request(
            messages=[{"role": "user", "content": f"Check this output data and heal or correct any errors observed: {data}. Response to be evaluated should be inside ['function_call']['arguments'].Let's think step by step."}],
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
##########
# DE DAT DROP LA ORICE UID CARE NU EXISTA IN LISTA INITIALA
#########

def filter_uids(processedResults, uid_to_id_mapping):
    # 1. Create an empty list to store the filtered results
    filteredResults = []

    for result_dict in processedResults:
        if not isinstance(result_dict, dict):
            continue
        new_dict = {}
        for key, value in result_dict.items():
            new_value_list = []
            for sub_dict in value:
                filtered_uids = [uid for uid in sub_dict['uid'] if uid in uid_to_id_mapping.keys()]
                if filtered_uids:
                    new_sub_dict = sub_dict.copy()
                    new_sub_dict['uid'] = filtered_uids
                    new_value_list.append(new_sub_dict)
            new_dict[key] = new_value_list
        filteredResults.append(new_dict)
    
    return filteredResults

# %%
filteredResults = filter_uids(processedResults, uid_to_id_mapping)


# %%
# Creeaza un dictionar cu un array de dictionare fiecare
print("changing dict structure")
processedData = {}
for item in filteredResults:
    try:
        key = list(item.keys())[0]
        value = list(item.values())[0]
        processedData[key] = value
    except IndexError:
        try:
            new_item = item[0]
            key = list(new_item.keys())[0]
            value = list(new_item.values())[0]
            processedData[key] = value
        except IndexError:
            print("Error: Item does not have keys or values.")
            print(item)
        except Exception as e:
            print(f"Unexpected error: {e}")
            print(item)
    except Exception as e:
        print(f"Unexpected error: {e}")
        print(item)

# %%

# Redenumeste cheile in 'label;
updatedOuterData = {}
for outer_key, inner_list in processedData.items():
    updatedInnerList = []
    for inner_dict in inner_list:
        updatedInnerDict = {}

        for key, value in inner_dict.items():
            if key == 'detailingSentence' or key == 'objectiveStatement':
                new_key = 'label'
            else:
                new_key = key
            updatedInnerDict[new_key] = value
        
        updatedInnerList.append(updatedInnerDict)
    
    updatedOuterData[outer_key] = updatedInnerList

processedData = updatedOuterData.copy()

###############
# %%
print("changing dict structure for reviews comprehension")
result = {}
for key, value_list in processedData.items():
    try:
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
    except KeyError as e:
        print(f"KeyError: Missing key {e} in dictionary.")
    
# Sort the result dictionary by 'uid' keys
sortedResult = {k: result[k] for k in sorted(result)}




# %%
print("Adding tags to reviews")
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

##########
# DE DAT DROP LA ORICE UID CARE NU EXISTA IN LISTA INITIALA
#########

# %%
# Add asin to each uid
print("Adding asin to each uid")
for key, value_list in processedData.items():
    for item in value_list:
        item['asin'] = [uid_to_asin[uid] for uid in item['uid']]


# %%

# Add rating to each uid
for key, value_list in processedData.items():
    for item in value_list:
        item['rating'] = [int(uid_to_rating[uid]) for uid in item['uid']]


# %%
print("Quantifying data")
try:
    quantifiedData = quantify_category_data(processedData)
except Exception as e:
    print(f"Error in quantifying data: {e}")
    quantifiedData = {}



# %%
# Add the text from the reviews to each label
print("Adding text to each label")
uid_to_text = {review['uid']: review['text'] for review in tagedReviews}

for key, value_list in quantifiedData.items():
    for item in value_list:
        item['customerVoice'] = [uid_to_text[uid] for uid in item['uid']]


# Add id to each uid
print("Adding id to each uid")
quantifiedDataId = quantifiedData.copy()
for key, value_list in quantifiedDataId.items():
    for item in value_list:
        item['id'] = [uid_to_id_mapping[uid] for uid in item['uid']]


# %%
# Prepare the Frontend dataset
try:
    frontendOutput = {
        key: [
            {
                k: entry[k] if k != 'uid' else entry[k][:5]
                for k in ['label', 'numberOfObservations', 'percentage', 'rating', 'uid']
            }
            for entry in value
        ]
        for key, value in quantifiedData.items()
    }
except KeyError as e:
    print(f"KeyError: Missing key {e} in dictionary.")
    frontendOutput = {}
except Exception as e:
    print(f"Unexpected error: {e}")
    frontendOutput = {}

try:
    for key, value_list in frontendOutput.items():
        for item in value_list:
            item['customerVoice'] = [uid_to_text[uid] for uid in item['uid']]
except KeyError as e:
    print(f"KeyError: Missing key {e} in dictionary.")
except Exception as e:
    print(f"Unexpected error: {e}")

try:
    frontendOutput = {
        key: [
            {
                k: entry[k]
                for k in ['label', 'numberOfObservations', 'percentage', 'rating', 'customerVoice']
            }
            for entry in value
        ]
        for key, value in frontendOutput.items()
    }
except KeyError as e:
    print(f"KeyError: Missing key {e} in dictionary.")
except Exception as e:
    print(f"Unexpected error: {e}")


# Sort each category's list based on 'numberOfObservations'
try:
    for key, value_list in frontendOutput.items():
        sorted_value_list = sorted(value_list, key=lambda x: x['numberOfObservations'], reverse=True)
        frontendOutput[key] = sorted_value_list
except KeyError as e:
    print(f"KeyError: Missing key {e} in dictionary.")
except Exception as e:
    print(f"Unexpected error: {e}")



# %%
import pandas as pd
import os
import json
from collections import defaultdict
import logging

from google.cloud import firestore, secretmanager
import firebase_admin
from firebase_admin import credentials, firestore

from tqdm import tqdm
import time


try:
    from src.investigations import get_asins_from_investigation, update_investigation_status
except ImportError:
    from investigations import get_asins_from_investigation, update_investigation_status

# %%

def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    project_id = "productexplorerdata"
    secret_version_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": secret_version_name})
    return response.payload.data.decode('UTF-8')

def initialize_firestore():
    """Initialize Firestore client."""

    # Check if running on App Engine
    if os.environ.get('GAE_ENV', '').startswith('standard'):
        # Running on App Engine, use default credentials
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
    else:
        # Try to get the key content from environment variable
        FIREBASE_KEY = os.getenv("FIREBASE_KEY")

        # If not found, try to get from secret management
        if not FIREBASE_KEY:
            try:
                FIREBASE_KEY = get_secret("FIREBASE_KEY")
            except Exception as e:
                logging.error(f"Error fetching FIREBASE_KEY from secret manager: {e}")

        # If still not found, load from .env (for local development)
        if not FIREBASE_KEY:
            from dotenv import load_dotenv
            load_dotenv()
            FIREBASE_KEY = os.getenv("FIREBASE_KEY")

        if not FIREBASE_KEY:
            raise ValueError("FIREBASE_KEY not found in environment or secrets")

        # Check if FIREBASE_KEY is a path to a file
        if os.path.exists(FIREBASE_KEY):
            with open(FIREBASE_KEY, 'r') as file:
                cred_data = json.load(file)
        else:
            # Try to parse the key content as JSON
            try:
                cred_data = json.loads(FIREBASE_KEY)
            except json.JSONDecodeError:
                logging.error("Failed to parse FIREBASE_KEY content")
                raise ValueError("Failed to parse FIREBASE_KEY as JSON")

        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_data)
            firebase_admin.initialize_app(cred)

    db = firestore.client()
    return db


# %%
def write_insights_to_firestore(userId, investigationId, quantifiedDataId, db):
    try:
        batch = db.batch()
        startTime = time.time()

        # Iterate over each category in quantifiedDataId
        for category, insights_list in quantifiedDataId.items():
            for insight in insights_list:
                # Ensure data types
                insight['numberOfObservations'] = int(insight['numberOfObservations'])
                insight['percentage'] = float(insight['percentage'])
                insight['rating'] = float(insight['rating'])

                # Create a unique document reference based on the label within the category
                doc_ref = db.collection(u'reviewsInsights').document(userId).collection('investigationCollections').document(investigationId).collection(category).document(insight['label'])
                batch.set(doc_ref, insight)

        batch.commit()
        endTime = time.time()
        elapsedTime = endTime - startTime
        logging.info(f"Quantified data for {investigationId} successfully written to Firestore. Time taken: {elapsedTime} seconds")
        return True
    except Exception as e:
        logging.error(f"Error writing quantified data for {investigationId} to Firestore: {e}")
        return False

# %%
# Initialize batch
batch = db.batch()

# Loop through each category in frontendOutput
for category, insights_list in frontendOutput.items():
    # Initialize counter for each category
    counter = 0
    
    for insight in insights_list:
        # Ensure data types
        insight['numberOfObservations'] = int(insight['numberOfObservations'])
        insight['percentage'] = float(insight['percentage'])
        insight['rating'] = float(insight['rating'])
        
        # Use counter as the document ID
        document_id = str(counter)
        
        # Create a unique document reference based on the counter within the category
        try:
            doc_ref = db.collection(u'reviewsInsights').document(str(userId)).collection('investigationCollections').document(str(investigationId)).collection(str(category)).document(document_id)
        except ValueError as e:
            print(f"An error occurred: {e}")
            continue  # Skip this iteration and continue with the next one
        
        # Add to batch
        batch.set(doc_ref, insight)
        
        # Increment counter
        counter += 1

# Commit the batch
try:
    batch.commit()
except Exception as e:
    print(f"An error occurred while committing the batch: {e}")










# %%
write_insights_to_firestore(userId, investigationId, frontendOutput, db)

# %%
write_reviews_to_firestore(tagedReviews, db)

# %%
update_investigation_status(userId, investigationId, 'finishedReviews', db)
# %%
