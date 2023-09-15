# ##################
# reviews_processing.py
# %%
import asyncio
from tqdm import tqdm
import time
import logging
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


####################################### PROCESS REVIEWS WITH GPT #######################################


def process_reviews_with_gpt(reviewsList, db):
    try:
        # Start the timer
        start_time = time.time()

        # Define review functions
        reviewFunctions = [
            {
                "name": "reviewDataFunction",
                "description": "product description",
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