#####################
# main.py
# %%
from flask import jsonify, request
import logging
import time
logging.basicConfig(level=logging.INFO)


try:
    from firebase_utils import FirestoreClient, PubSubClient, GAEClient, start_investigation
except ImportError as e:
    logging.error(f"import error is {e}")

try:
    from data_acquisition import execute_data_acquisition
except ImportError as e:
    logging.error(f"import  error is {e}")

try:
    from run_investigation import run_end_to_end_investigation, ensure_event_loop
except ImportError as e:
    logging.error(f"import error is {e}")

try:
    from reviews_processing import run_reviews_investigation
except ImportError as e:
    logging.error(f"import error is {e}")

try:
    db = FirestoreClient.get_instance()
except Exception as e:
    logging.error(f"Error initializing Firestore: {e}")

try:
    publisher, subscriber, project_id, topic_id, subscription_id, topic_path, subscription_path = PubSubClient.get_instance()
except Exception as e:
    logging.error(f"Error initializing Pub/Sub: {e}")

try:
    GAEClient.get_instance()
except Exception as e:
    logging.error(f"Error initializing GAE: {e}")


# %%
# logging.info("This is an info message.")
# logging.warning("This is a warning message.")
# logging.error("This is an error message.")
# %%


def api_start_investigation():
    """
    Initiates a new investigation based on the provided user ID and list of ASINs.
    """
    data = request.json
    userId = data.get('userId')
    asinList = data.get('asinList')
    name = data.get('name')
    
    if not userId or not asinList or not name:
        return jsonify({"error": "userIDs and asinList are required"}), 400

    """    
    try:
        initialize_firestore()
    except Exception as e:
        logging.error(f"Error initializing Firestore: {e}")

    try:
        initialize_gae()
    except Exception as e:
        logging.error(f"Error initializing GAE: {e}")

    try:
        initialize_pub_sub()
    except Exception as e:
        logging.error(f"Error initializing Pub/Sub: {e}") 
        
    """


    try:
        result = start_investigation(data)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def api_run_data_acquisition():
    """
    Initiates data acquisition based on the provided list of ASINs.
    """

    """    
    try:
        initialize_firestore()
    except Exception as e:
        logging.error(f"Error initializing Firestore: {e}")

    try:
        initialize_gae()
    except Exception as e:
        logging.error(f"Error initializing GAE: {e}")

    try:
        initialize_pub_sub()
    except Exception as e:
        logging.error(f"Error initializing Pub/Sub: {e}")

    """    


    try:
        data = request.json
        if not data:
            logging.error("No JSON payload received for data acquisition")
            return jsonify({"error": "No JSON payload received"}), 400

        asinList = data.get('asinList')
        
        if not asinList:
            logging.error("Missing asinList for data acquisition")
            return jsonify({"error": "asinList is required"}), 400

        if not isinstance(asinList, list) or len(asinList) == 0:
            logging.error("asinList should be a non-empty list")
            return jsonify({"error": "asinList should be a non-empty list"}), 400

        logging.info(f"Starting data acquisition for ASINs: {asinList}")
        result = execute_data_acquisition(asinList)
        
        if result:
            logging.info("Data acquisition completed successfully")
            return jsonify({"message": "Data acquisition completed successfully"}), 200
        else:
            logging.error("Data acquisition failed")
            return jsonify({"error": "Data acquisition failed"}), 500

    except Exception as e:
        logging.error(f"An exception occurred during data acquisition: {str(e)}")
        return jsonify({"error": str(e)}), 500



def api_run_reviews_investigation():
    """
    Initiates a reviews investigation based on the provided investigation ID and credential path.
    """

    """    
    try:
        initialize_firestore()
    except Exception as e:
        logging.error(f"Error initializing Firestore: {e}")

    try:
        initialize_gae()
    except Exception as e:
        logging.error(f"Error initializing GAE: {e}")

    try:
        initialize_pub_sub()
    except Exception as e:
        logging.error(f"Error initializing Pub/Sub: {e}")

    """    



    data = request.json
    investigationId = data.get('investigationId')
    userId = data.get('userId')
    
    if not investigationId:
        logging.error("Missing investigationId")
        return jsonify({"error": "investigationId is required"}), 400

    try:
        logging.info(f"Starting reviews investigation for ID: {investigationId}")
        run_reviews_investigation(userId, investigationId)
        logging.info(f"Completed reviews investigation for ID: {investigationId}")
        return jsonify({"message": "Reviews investigation completed successfully"}), 200
    except Exception as e:
        logging.error(f"Failed to complete reviews investigation for ID: {investigationId}. Error: {str(e)}")
        return jsonify({"error": str(e)}), 500



from run_investigation import run_end_to_end_investigation, ensure_event_loop  # Ensure this is correctly imported

def api_run_end_to_end_investigation():
    """
    Initiates an end-to-end investigation based on the provided user ID and list of ASINs.
    """
    start_time = time.time()  # Start the timer

    try:
        data = request.json
        userId = data.get('userId')
        asinList = data.get('asinList')
        name = data.get('name')

        if not userId or not asinList or not name:
            return jsonify({"error": "userId and asinList and name are required"}), 400

        ensure_event_loop()  # Ensure an event loop is available for async operations

        result = run_end_to_end_investigation(data)  # If this function is async, ensure it's awaited properly or run via asyncio.run() if it's the main async entry point

        if result:
            end_time = time.time()  # Stop the timer
            elapsed_time = end_time - start_time
            logging.info(f"Total time taken for end-to-end investigation: {elapsed_time:.2f} seconds")

            return jsonify({"message": "End-to-end investigation completed successfully"}), 200
        else:
            return jsonify({"error": "End-to-end investigation failed"}), 500

    except Exception as e:
        logging.error(f"Error in api_run_end_to_end_investigation: {e}")
        return jsonify({"error": str(e)}), 500


# %%