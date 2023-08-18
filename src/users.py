#####################
# users.py
import firebase_admin
from firebase_admin import firestore

def get_user_ref(user_id, db):
    """Return a reference to a user document."""
    return db.collection('users').document(user_id)

def create_user(user_data, db):
    """Create a new user in the database."""
    user_ref = db.collection('users').document()
    user_id = user_ref.id
    user_data['id'] = user_id
    user_ref.set(user_data)
    return user_id

def get_user(user_id, db):
    """Retrieve user data from the database."""
    try:
        user_ref = get_user_ref(user_id, db).get()
        if user_ref.exists:
            return user_ref.to_dict()
        else:
            return None  # or raise a custom exception
    except Exception as e:
        # Log the error or raise a custom exception
        print(f"Error fetching user {user_id}: {e}")
        return None

def subscribe_user(user_id, package, db):
    """Subscribe a user to a package."""
    user_ref = get_user_ref(user_id, db)
    subscription_ref = user_ref.collection('subscriptions').document()
    subscription_id = subscription_ref.id
    subscription_data = {
        'id': subscription_id,
        'user_id': user_id,
        'package': package,
        'start_date': firestore.SERVER_TIMESTAMP,
    }
    subscription_ref.set(subscription_data)
    return subscription_data

def log_payment(payment_data, db):
    """Log a payment in the database."""
    payment_ref = db.collection('payments').document() 
    payment_id = payment_ref.id
    payment_data['id'] = payment_id
    payment_ref.set(payment_data)
    return payment_id

def subscribe_user_to_package(user_id, package, start_date, payment_intent_id, db):
    """Subscribe a user to a package and update their investigation count."""
    user_ref = get_user_ref(user_id, db)
    subs = user_ref.collection('subscriptions').document()
    subs.set({
        'package': package,
        'start_date': start_date,
        'payment_status': 'pending',
        'payment_intent': payment_intent_id,
    })
    user_ref.update({
        'current_package': package,
        'remaining_investigation': 50 if package == 'basic' else 100,
    })

def use_investigation(user_id, db):
    """Decrement the user's investigation count by one."""
    user_ref = get_user_ref(user_id, db)
    user = user_ref.get()
    remaining = user.get('remaining_investigation')
    if remaining > 0:
        user_ref.update({
            'remaining_investigation': firestore.Increment(-1),
        })
        return True
    else:
        return False

def add_investigation(user_id, asins, db):
    """Add an investigation for the user."""
    user_ref = get_user_ref(user_id, db)
    user = user_ref.get()
    remaining = user.get('remaining_investigations')
    if remaining > 0:
        investigation_ref = db.collection('investigations').document()
        investigation_ref.set({
            'user_id': user_id,
            'received_timestamp': firestore.SERVER_TIMESTAMP,
            'asins': asins,
            'status': 'received',
            'started_timestamp': None,
            'finished_timestamp': None,
            'reviewed_timestamps': [],
        })
        user_ref.update({
            'remaining_investigations': firestore.Increment(-1),
        })
        return True
    else:
        return False

def update_investigation_status(investigation_id, new_status, db):
    """Update the status of an investigation."""
    investigation_ref = db.collection('investigations').document(investigation_id)
    investigation = investigation_ref.get()
    if investigation.exists:
        investigation_ref.update({
            'status': new_status,
            f'{new_status}_timestamp': firestore.SERVER_TIMESTAMP,
        })
        return True
    else:
        return False

def log_investigation_review(investigation_id, db):
    """Log a review timestamp for a finished investigation."""
    investigation_ref = db.collection('investigations').document(investigation_id)
    investigation = investigation_ref.get()
    if investigation.exists and investigation.get('status') == 'finished':
        investigation_ref.update({
            'reviewed_timestamps': firestore.ArrayUnion([firestore.SERVER_TIMESTAMP]),
        })
        return True
    else:
        return False

def has_investigations_available(user_id, db):
    """Check if a user has available investigations."""
    user_ref = get_user_ref(user_id, db).get()
    remaining = user_ref.get('remaining_investigations')
    return remaining > 0

# Usage example
#user_id = '...'
#if has_investigations_available(user_id, db):
#    asins = ['B0BCTTCSBZ', 'B0BLNBS36G', 'B0BW8Y2B8Z', 'B091325ZMB']
#    add_investigation(user_id, asins, db)
#else:
#    print('User has no remaining investigations')

# ===========================