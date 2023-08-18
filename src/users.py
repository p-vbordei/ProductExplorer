#####################
# users.py
import firebase_admin
from firebase_admin import firestore

def get_user_ref(userId, db):
    """Return a reference to a user document."""
    return db.collection('users').document(userId)

def create_user(userData, db):
    """Create a new user in the database."""
    user_ref = db.collection('users').document()
    userId = user_ref.id
    userData['id'] = userId
    user_ref.set(userData)
    return userId

def get_user(userId, db):
    """Retrieve user data from the database."""
    try:
        user_ref = get_user_ref(userId, db).get()
        if user_ref.exists:
            return user_ref.to_dict()
        else:
            return None  # or raise a custom exception
    except Exception as e:
        # Log the error or raise a custom exception
        print(f"Error fetching user {userId}: {e}")
        return None

def subscribe_user(userId, package, db):
    """Subscribe a user to a package."""
    user_ref = get_user_ref(userId, db)
    subscription_ref = user_ref.collection('subscriptions').document()
    subscriptionId = subscription_ref.id
    subscriptionData = {
        'id': subscriptionId,
        'userId': userId,
        'package': package,
        'startDate': firestore.SERVER_TIMESTAMP,
    }
    subscription_ref.set(subscriptionData)
    return subscriptionData

def log_payment(paymentData, db):
    """Log a payment in the database."""
    payment_ref = db.collection('payments').document() 
    paymentId = payment_ref.id
    paymentData['id'] = paymentId
    payment_ref.set(paymentData)
    return paymentId

def subscribe_user_to_package(userId, package, startDate, paymentIntentId, db):
    """Subscribe a user to a package and update their investigation count."""
    user_ref = get_user_ref(userId, db)
    subs = user_ref.collection('subscriptions').document()
    subs.set({
        'package': package,
        'startDate': startDate,
        'paymentStatus': 'pending',
        'paymentIntent': paymentIntentId,
    })
    user_ref.update({
        'currentPackage': package,
        'remainingInvestigations': 50 if package == 'basic' else 100,
    })

def use_investigation(userId, db):
    """Decrement the user's investigation count by one."""
    user_ref = get_user_ref(userId, db)
    user = user_ref.get()
    remaining = user.get('remainingInvestigations')
    if remaining > 0:
        user_ref.update({
            'remainingInvestigations': firestore.Increment(-1),
        })
        return True
    else:
        return False

def add_investigation(userId, asins, db):
    """Add an investigation for the user."""
    user_ref = get_user_ref(userId, db)
    user = user_ref.get()
    remaining = user.get('remainingInvestigations')
    if remaining > 0:
        investigation_ref = db.collection('investigations').document()
        investigation_ref.set({
            'userId': userId,
            'receivedTimestamp': firestore.SERVER_TIMESTAMP,
            'asins': asins,
            'status': 'received',
            'startedTimestamp': None,
            'finishedTimestamp': None,
            'reviewedTimestamps': [],
        })
        user_ref.update({
            'remainingInvestigations': firestore.Increment(-1),
        })
        return True
    else:
        return False

def update_investigation_status(investigationId, newStatus, db):
    """Update the status of an investigation."""
    investigation_ref = db.collection('investigations').document(investigationId)
    investigation = investigation_ref.get()
    if investigation.exists:
        investigation_ref.update({
            'status': newStatus,
            f'{newStatus}Timestamp': firestore.SERVER_TIMESTAMP,
        })
        return True
    else:
        return False

def log_investigation_review(investigationId, db):
    """Log a review timestamp for a finished investigation."""
    investigation_ref = db.collection('investigations').document(investigationId)
    investigation = investigation_ref.get()
    if investigation.exists and investigation.get('status') == 'finished':
        investigation_ref.update({
            'reviewedTimestamps': firestore.ArrayUnion([firestore.SERVER_TIMESTAMP]),
        })
        return True
    else:
        return False

def has_investigations_available(userId, db):
    """Check if a user has available investigations."""
    user_ref = get_user_ref(userId, db).get()
    remaining = user_ref.get('remainingInvestigations')
    return remaining > 0


# =====================