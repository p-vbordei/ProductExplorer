##################
# run_investigation.py
# The scope of this file is to run end the end-to-end investigation process.
# It will start an investigation, run data acquisition, run products processing, and run reviews processing.


try:
    from src import app, connex_app
    from src.firebase_utils import initialize_firestore
    from src.investigations import start_investigation
    from src.data_acquisition import execute_data_acquisition
    from src.products_processing import run_products_investigation
    from src.reviews_processing import run_reviews_investigation
except ImportError:
    from firebase_utils import initialize_firestore
    from investigations import start_investigation
    from data_acquisition import execute_data_acquisition
    from products_processing import run_products_investigation
    from reviews_processing import run_reviews_investigation



# %%

def run_end_to_end_investigation(data):
    try:
        db = initialize_firestore()
    except Exception as e:
        print(f"Error initializing Firestore: {e}")
        return False

    try:
        investigationData = start_investigation(data, db)
        if not investigationData:
            print("Failed to start the investigation.")
            return False
        print('Investigation started successfully')
    except Exception as e:
        print(f"Error starting the investigation: {e}")
        return False

    asins = investigationData.get('asins')
    investigationId = investigationData.get('id')

    if not asins:
        print("No ASINs found for the investigation.")
        return False

    try:
        execute_data_acquisition(asins)
        print('Data acquisition completed successfully')
    except Exception as e:
        print(f"Error during data acquisition: {e}")
        return False

    try:
        run_products_investigation(investigationId)
        print('Products processing completed successfully')
    except Exception as e:
        print(f"Error during products processing: {e}")
        return False

    try:
        run_reviews_investigation(investigationId)
        print('Reviews processing completed successfully')
    except Exception as e:
        print(f"Error during reviews processing: {e}")
        return False

    return True



#%%
# ====================