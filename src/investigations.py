#####################
# investigations.py

import firebase_admin
from firebase_admin import firestore

def start_investigation(data, db):
    """Start a new investigation with given data."""
    try:
        userId = data.get('userId')
        asinList = data.get('asinList')

        if not userId or not asinList:
            raise ValueError("userId and asinList are required fields.")

        investigation_ref = db.collection('investigations').document()
        investigationId = investigation_ref.id

        investigation_data = {
            'id': investigationId,
            'userId': userId,
            'asinList': asinList,
            'status': 'started',
            'startTimestamp': 'Pending Firestore Timestamp',
        }

        investigation_ref.set({
            'id': investigationId,
            'userId': userId,
            'asinList': asinList,
            'status': 'started',
            'startTimestamp': firestore.SERVER_TIMESTAMP,
        })
        return investigation_data
    except KeyError:
        raise ValueError("The data dictionary is missing required keys.")
    except Exception as e:
        print(f"Error starting investigation: {e}")
        return None

def get_investigation(investigationId, db):
    """Retrieve investigation data by its ID."""
    try:
        investigation_ref = db.collection('investigations').document(investigationId).get()
        if investigation_ref.exists:
            data = investigation_ref.to_dict()
            if 'startTimestamp' in data and data['startTimestamp'] == firestore.SERVER_TIMESTAMP:
                data['startTimestamp'] = 'Pending Firestore Timestamp'
            return data
        else:
            raise ValueError(f"Investigation with ID {investigationId} does not exist.")
    except Exception as e:
        print(f"Error fetching investigation {investigationId}: {e}")
        return None

def complete_investigation(investigationId, results, db):
    """Mark an investigation as completed and store its results."""
    if not results:
        raise ValueError("Results are required to complete the investigation.")

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

def update_investigation_status(investigationId, newStatus, db):
    if not newStatus:
        raise ValueError("New status is required to update the investigation.")

    investigation_ref = db.collection('investigations').document(investigationId)
    investigation = investigation_ref.get()
    if investigation.exists:
        investigation_ref.update({
            'status': newStatus,
            f'{newStatus}Timestamp': firestore.SERVER_TIMESTAMP,
        })
        return True
    else:
        raise ValueError(f"Investigation with ID {investigationId} does not exist.")

def get_asins_from_investigation(investigationId, db):
    investigation_ref = db.collection('investigations').document(investigationId)
    investigation = investigation_ref.get()

    if investigation.exists:
        asinList = investigation.get('asinList')
        if asinList:
            return asinList
        else:
            raise ValueError(f"Investigation with ID {investigationId} does not have any ASINs.")
    else:
        raise ValueError(f"Investigation with ID {investigationId} does not exist.")


# ===========================