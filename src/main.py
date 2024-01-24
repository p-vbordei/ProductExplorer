#####################
# main.py
# %%
from flask import jsonify, request
import os
import logging
import time
logging.basicConfig(level=logging.INFO)

try:
    try:
        from src import connex_app
    except ImportError:
        import connex_app
except:
    print("connex_app import failed")
    pass

try:
    try:
        from src import app
    except ImportError:
        import app
except:
    print("app import failed for src")
    pass


try:
    try:
        from . import app
    except ImportError:
        import app
except:
    print("app import failed for dot")
    pass



try:
    from src.investigations import start_investigation
    from src.data_acquisition import execute_data_acquisition
    from src.reviews_processing import run_reviews_investigation
    from src.run_investigation import run_end_to_end_investigation
    from src.firebase_utils import FirestoreClient, PubSubClient, GAEClient, SecretManager
except ImportError:
    from investigations import start_investigation
    from data_acquisition import execute_data_acquisition
    from reviews_processing import run_reviews_investigation
    from run_investigation import run_end_to_end_investigation
    from firebase_utils import FirestoreClient, PubSubClient, GAEClient, SecretManager


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
logging.info("This is an info message.")
logging.warning("This is a warning message.")
logging.error("This is an error message.")
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



def api_run_end_to_end_investigation():
    """
    Initiates an end-to-end investigation based on the provided user ID and list of ASINs.
    """
    start_time = time.time()  # Start the timer

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
        userId = data.get('userId')
        asinList = data.get('asinList')
        name = data.get('name')

        if not userId or not asinList or not name:
            return jsonify({"error": "userId and asinList and name are required"}), 400

        result = run_end_to_end_investigation(data)

        if result:
            end_time = time.time()  # Stop the timer
            elapsed_time = end_time - start_time
            logging.info(f"Total time taken for end-to-end investigation: {elapsed_time:.2f} seconds")  # Log the elapsed time

            return jsonify({"message": "End-to-end investigation completed successfully"}), 200
        else:
            return jsonify({"error": "End-to-end investigation failed"}), 500

    except Exception as e:
        logging.error(f"Error in api_run_end_to_end_investigation: {e}")  # Log the error
        return jsonify({"error": str(e)}), 500

# %%

if __name__ == "__main__":
    connex_app.run(port=8080, debug = True)
# ====================================
# %%
