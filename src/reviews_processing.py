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


        # %%



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
        #################################################
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
                "description": "Naming follows the JTBD framework. Group reviews on topics for each type of job and be sure to that each label is described in two sentences. Extract associated review ids. Let's think step by step.",
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
        
        filteredResults = filter_uids(processedResults, uid_to_id_mapping)

        ##################
        # %%

        # Rezultatul este o lista de dictionare in loc de un dictionar


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
                    try:
                        label = value['detailingSentence']
                    except:
                        try:
                            label = value['objectiveStatement']
                        except:
                            try:
                                label = value['label']
                            except:
                                pass
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


        return tagedReviews, frontendOutput

    except Exception as e:
        logging.error(f"Error in process_reviews_with_gpt: {e}")
        return None, None  # Return None in case of error

# %%




def run_reviews_investigation(userId: str, investigationId: str) -> None:
    db = initialize_firestore()
    if not db:
        logging.error("Error initializing Firestore.")
        return

    if not update_investigation_status(userId, investigationId, 'startedReviews', db):
        logging.error(f"Error updating investigation status to 'startedReviews'.")
        return

    reviews = get_clean_reviews(userId, investigationId, db)
    print('Processing ', len(reviews), ' reviews')
    if not reviews:
        logging.error("Error getting clean reviews.")
        return

    tagedReviews, frontendOutput = process_reviews_with_gpt(reviews, db)
    if not tagedReviews or not frontendOutput:
        logging.error("Error processing reviews with GPT.")
        return
    
    if not write_insights_to_firestore(userId, investigationId, frontendOutput, db):
        logging.error("Error writing quantified data to Firestore.")
        return
    
    """
    if not write_reviews_to_firestore(tagedReviews, db):
        logging.error("Error writing processed reviews to Firestore.")
        return
    """

    if not update_investigation_status(userId, investigationId, 'finishedReviews', db):
        logging.error(f"Error updating investigation status to 'finishedReviews'.")
        return

    logging.info(f"Reviews investigation for UserId: {userId} and InvestigationId: {investigationId} completed successfully.")
# %%
