# ##################
# reviews_processing.py
# %%
import asyncio
from tqdm import tqdm
import time
import logging
import pandas as pd
logging.basicConfig(level=logging.INFO)
import json

import aiohttp
import os
import tiktoken
import nest_asyncio
nest_asyncio.apply()



try:
    from src import app
    from src.reviews_data_processing_utils import generate_batches, add_uid_to_reviews, aggregate_all_categories,  quantify_category_data, export_functions_for_reviews
    from src.firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, write_insights_to_firestore
    from src.openai_utils import chat_completion_request, get_completion_list_multifunction, ProgressLog, get_completion
    from src.investigations import update_investigation_status
except ImportError:
    from reviews_data_processing_utils import generate_batches, add_uid_to_reviews, aggregate_all_categories,  quantify_category_data, export_functions_for_reviews
    from firebase_utils import initialize_firestore, get_clean_reviews , write_reviews_to_firestore, write_insights_to_firestore
    from openai_utils import chat_completion_request, get_completion_list_multifunction, ProgressLog, get_completion
    from investigations import update_investigation_status


# %%


userId = "46NVFvZbVLgQk2gOSY4tOD0NChH2"
investigationId = "B8QYdlDty2SPoyloJaxt"

db = initialize_firestore()


if not update_investigation_status(userId, investigationId, 'startedReviews', db):
    logging.error(f"Error updating investigation status to 'startedReviews'.")


reviews = get_clean_reviews(userId, investigationId, db)
print('Processing ', len(reviews), ' reviews')
if not reviews:
    logging.error("Error getting clean reviews.")

# %%


reviewsList = reviews.copy()
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
marketFunctions,  extractJobsFunctions, marketResponseHealFunction, useCaseFunction, productComparisonFunction, featureRequestFunction, painPointsFunction, usageFrequencyFunction, usageTimeFunction, usageLocationFunction, customerDemographicsFunction, functionalJobFunction, socialJobFunction, emotionalJobFunction, supportingJobFunction = export_functions_for_reviews()


# %%



# %%
# Run GPT Calls for the Market function on the batches

functionsList = [marketFunctions, extractJobsFunctions]
functionsCallList = [{"name": "market"}, {"name": "extractJobs"}]
GPT_MODEL = 'gpt-3.5-turbo-16k'

# Get responses from GPT
async def main_for_data_extraction():
    responses = await get_completion_list_multifunction(contentList, functions_list=functionsList, function_calls_list=functionsCallList, GPT_MODEL=GPT_MODEL)
    return responses

responses = asyncio.run(main_for_data_extraction())
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



# %%



# %%
GPT_MODEL = 'gpt-3.5-turbo-16k'
async def main_for_data_aggregation():
    
    semaphore = asyncio.Semaphore(10)  # Adjust as needed
    async with aiohttp.ClientSession() as session:
        functionsResponses = []
        for key, function in functionMapping.items():
            if key in aggregatedResponses:
                contentList = [
                    {"role": "user", "content": f"You are the most awesome product researcher. Please process the results for key: {key}.  \n Aggregated observations are here: {aggregatedResponses[key]}"}
                ]
                print({"name": function[0]["name"]})

                # Replace with the async call
                progress_log = ProgressLog(len(contentList))
                response = await get_completion(contentList, session, semaphore, progress_log, functions=function, function_call={"name": function[0]["name"]}, TEMPERATURE=0.3)
                
                functionsResponses.append(response)

    return functionsResponses

functionsResponses = asyncio.run(main_for_data_aggregation())

# %%
# Processes Results
processedResults = []
for index in range(len(functionsResponses)):
    try:
        print(index)
        item = functionsResponses[index]
        data = item['function_call']['arguments']
        # Try to parse the response data
        try:
            evalData = json.loads(data)
        except:
            healingResponse = chat_completion_request(
                messages=[{"role": "user", "content": f"Check this output data and heal or correct any errors observed: {data}. Response to be evaluated should be inside ['function_call']['arguments']."}],
                functions=marketResponseHealFunction,
                function_call={"name": "formatEnforcementAndHeal"},
                temperature=0,
                model=GPT_MODEL,
                TEMPERATURE = 0,
            )
            resp = healingResponse.json()['choices']
            parsed_resp = resp[0]['message']['function_call']['arguments']
            try:
                evalData = json.loads(parsed_resp)
            except:
                print(f"Error processing response including healing action for batch {index}.")
                pass
        processedResults.append(evalData)
    except:
        print(f"Error processing response for batch {index}.")
        pass

# %%

def filter_uids(processedResults, uid_to_id_mapping):
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

# %%

# Initialize an empty list to hold the new filtered results
newFilteredResults = []

# Loop through each dictionary in the original filteredResults list
for result_dict in filteredResults:
    # Create a new dictionary to store the de-duplicated lists for each key
    new_dict = {}
    
    for key, value_list in result_dict.items():
        # Initialize a set to keep track of seen items
        seen = set()
        
        # Initialize a list to keep the unique items
        unique_list = []
        
        for item in value_list:
            # Serialize the dictionary to a string to make it hashable
            item_str = json.dumps(item, sort_keys=True)
            
            # Add item to unique_list if not seen before
            if item_str not in seen:
                unique_list.append(item)
                seen.add(item_str)
        
        # Update the list for the current key with the de-duplicated list
        new_dict[key] = unique_list
    
    # Add the new dictionary with all de-duplicated lists to the new filtered list
    newFilteredResults.append(new_dict)


# Update filteredResults with the de-duplicated results
filteredResults = newFilteredResults


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

# %%

# Redenumeste cheile in 'header;
updatedOuterData = {}
for outer_key, inner_list in processedData.items():
    updatedInnerList = []
    for inner_dict in inner_list:
        updatedInnerDict = {}

        for key, value in inner_dict.items():
            if key == 'headerOfCategory (7 words)' or key == 'objectiveStatement' or key == 'headerOfCategory':
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
                label = value['headerOfCategory (7 words)']
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
# Add the text from the reviews to each header
print("Adding text to each header")
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

if not write_insights_to_firestore(userId, investigationId, frontendOutput, db):
    logging.error("Error writing quantified data to Firestore.")

# %%

if not update_investigation_status(userId, investigationId, 'finishedReviews', db):
    logging.error(f"Error updating investigation status to 'finishedReviews'.")


logging.info(f"Reviews investigation for UserId: {userId} and InvestigationId: {investigationId} completed successfully.")
# %%
