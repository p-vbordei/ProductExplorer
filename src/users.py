#####################
# users.py
import firebase_admin
from firebase_admin import firestore

import logging
logging.basicConfig(level=logging.INFO)

def get_user_ref(userId, db):
    try:
        return db.collection('users').document(userId)
    except Exception as e:
        logging.error(f"Error getting user reference for {userId}: {e}")
        return None

def create_user(userData, db):
    try:
        user_ref = db.collection('users').document()
        userId = user_ref.id
        userData['id'] = userId
        user_ref.set(userData)
        return userId
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return None

def get_user(userId, db):
    try:
        user_ref = get_user_ref(userId, db).get()
        if user_ref.exists:
            return user_ref.to_dict()
        else:
            return None
    except Exception as e:
        logging.error(f"Error fetching user {userId}: {e}")
        return None

def subscribe_user(userId, package, db):
    try:
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
    except Exception as e:
        logging.error(f"Error subscribing user {userId} to package {package}: {e}")
        return None

def log_payment(paymentData, db):
    try:
        payment_ref = db.collection('payments').document()
        paymentId = payment_ref.id
        paymentData['id'] = paymentId
        payment_ref.set(paymentData)
        return paymentId
    except Exception as e:
        logging.error(f"Error logging payment: {e}")
        return None

def subscribe_user_to_package(userId, package, startDate, paymentIntentId, db):
    try:
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
    except Exception as e:
        logging.error(f"Error subscribing user {userId} to package {package}: {e}")


########### Investigation Related ##############

def use_investigation(userId, db):
    try:
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
    except Exception as e:
        logging.error(f"Error using investigation for user {userId}: {e}")
        return False

def add_investigation(userId, asinList, db):
    try:
        user_ref = get_user_ref(userId, db)
        user = user_ref.get()
        remaining = user.get('remainingInvestigations')
        if remaining > 0:
            investigation_ref = db.collection('investigations').document()
            investigation_ref.set({
                'userId': userId,
                'receivedTimestamp': firestore.SERVER_TIMESTAMP,
                'asinList': asinList,
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
    except Exception as e:
        logging.error(f"Error adding investigation for user {userId}: {e}")
        return False

def update_investigation_status(investigationId, newStatus, db):
    try:
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
    except Exception as e:
        logging.error(f"Error updating investigation status for {investigationId}: {e}")
        return False

def log_investigation_review(investigationId, db):
    try:
        investigation_ref = db.collection('investigations').document(investigationId)
        investigation = investigation_ref.get()
        if investigation.exists and investigation.get('status') == 'finished':
            investigation_ref.update({
                'reviewedTimestamps': firestore.ArrayUnion([firestore.SERVER_TIMESTAMP]),
            })
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Error logging investigation review for {investigationId}: {e}")
        return False

def has_investigations_available(userId, db):
    try:
        user_ref = get_user_ref(userId, db).get()
        remaining = user_ref.get('remainingInvestigations')
        return remaining > 0
    except Exception as e:
        logging.error(f"Error checking available investigations for user {userId}: {e}")
        return False

# =====================