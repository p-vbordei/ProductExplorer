
# investigations.py

import firebase_admin
from firebase_admin import firestore

def start_investigation(data, db):
    """Start a new investigation with given data."""
    try:
        user_id = data['user_id']
        asins = data['asins']
        
        investigation_ref = db.collection('investigations').document()
        investigation_id = investigation_ref.id
        
        investigation_data = {
            'id': investigation_id,
            'user_id': user_id,
            'asins': asins,
            'status': 'started',
            'start_timestamp': firestore.SERVER_TIMESTAMP,
        }
        
        investigation_ref.set(investigation_data)
        return investigation_data
    except KeyError:
        # Handle missing keys in data
        raise ValueError("The data dictionary is missing required keys.")
    except Exception as e:
        # Handle other exceptions
        print(f"Error starting investigation: {e}")
        return None

def get_investigation(investigation_id, db):
    """Retrieve investigation data by its ID."""
    try:
        investigation_ref = db.collection('investigations').document(investigation_id).get()
        if investigation_ref.exists:
            return investigation_ref.to_dict()
        else:
            return None
    except Exception as e:
        print(f"Error fetching investigation {investigation_id}: {e}")
        return None

def complete_investigation(investigation_id, results, db):
    """Mark an investigation as completed and store its results."""
    try:
        investigation_ref = db.collection('investigations').document(investigation_id)
        investigation_ref.update({
            'status': 'completed',
            'results': results,
            'end_timestamp': firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception as e:
        print(f"Error completing investigation {investigation_id}: {e}")
        return False
