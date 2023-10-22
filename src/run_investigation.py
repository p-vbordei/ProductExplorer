##################
# run_investigation.py
# The scope of this file is to run end the end-to-end investigation process.
# It will start an investigation, run data acquisition, run products processing, and run reviews processing.
import logging
logging.basicConfig(level=logging.INFO)

try:
    from src import app, connex_app
    from src.investigations import start_investigation
    from src.data_acquisition import execute_data_acquisition
    from src.reviews_processing import run_reviews_investigation
    from src.users import use_investigation, update_investigation_status
except ImportError:
    from investigations import start_investigation
    from data_acquisition import execute_data_acquisition
    from reviews_processing import run_reviews_investigation
    from users import use_investigation,  update_investigation_status


# %%

def run_end_to_end_investigation(data):
    try:
        investigationData = start_investigation(data)
        if not investigationData:
            print("Failed to start the investigation.")
            return False
        print('Investigation started successfully')
    except Exception as e:
        print(f"Error starting the investigation: {e}")
        return False

    asinList = investigationData.get('asinList')
    userId = investigationData.get('userId')
    investigationId = investigationData.get('id')

    if not asinList:
        print("No ASINs found for the investigation.")
        return False
    
    """    try:
            has_investigations_available(userId, db)
        except Exception as e:
            print(f"Error checking user {userId} for available investigations: {e}")
            return False
    """

    try:
        execute_data_acquisition(asinList)
        print('Data acquisition completed successfully')
    except Exception as e:
        print(f"Error during data acquisition: {e}")
        return False


    try:
        run_reviews_investigation(userId, investigationId)
        print('Reviews processing completed successfully')
    except Exception as e:
        print(f"Error during reviews processing: {e}")
        return False
    
    try:
        update_investigation_status(userId, investigationId, "finished")
        print('Investigation completed successfully')
    except Exception as e:
        print(f"Error during updating investigation status: {e}")
        return False

    """
    try:
        use_investigation(userId, db)
        print(f'Used Investigation from user: {userId}')
    except Exception as e:
        print(f"Error during using for user: {userId} ,investigation: {e}")
        return False
    return True
    """
#%%
# ====================