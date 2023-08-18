#####################
# investigations.py

import firebase_admin
from firebase_admin import firestore

def start_investigation(data, db):
    """Start a new investigation with given data."""
    try:
        userId = data['userId']
        asins = data['asins']
        
        investigation_ref = db.collection('investigations').document()
        investigationId = investigation_ref.id
        
        investigation_data = {
            'id': investigationId,
            'userId': userId,
            'asins': asins,
            'status': 'started',
            'startTimestamp': firestore.SERVER_TIMESTAMP,
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

def get_investigation(investigationId, db):
    """Retrieve investigation data by its ID."""
    try:
        investigation_ref = db.collection('investigations').document(investigationId).get()
        if investigation_ref.exists:
            return investigation_ref.to_dict()
        else:
            return None
    except Exception as e:
        print(f"Error fetching investigation {investigationId}: {e}")
        return None

def complete_investigation(investigationId, results, db):
    """Mark an investigation as completed and store its results."""
    try:
        investigation_ref = db.collection('investigations').document(investigationId)
        investigation_ref.update({
            'status': 'completed',
            'results': results,
            'endTimestamp': firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception as e:
        print(f"Error completing investigation {investigationId}: {e}")
        return False

def update_investigation_status(investigationId, newStatus,db):
    investigation_ref = db.collection(u'investigations').document(investigationId)
    investigation = investigation_ref.get()
    if investigation.exists:
        investigation_ref.update({
            'status': newStatus,
            f'{newStatus}Timestamp': firestore.SERVER_TIMESTAMP,
        })
        return True  # update was successful
    else:
        return False  # investigation does not exist

def get_asins_from_investigation(investigationId, db):
    # Retrieve the investigation from Firestore
    investigation_ref = db.collection(u'investigations').document(investigationId)
    investigation = investigation_ref.get()

    if investigation.exists:
        # Retrieve the asins from the investigation
        asins = investigation.get('asins')
        return asins
    else:
        print('Investigation does not exist')
        return None

# ===========================