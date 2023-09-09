import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('/Users/vladbordei/Documents/Development/ProductExplorer/notebooks/productexplorerdata-firebase-adminsdk-ulb3d-465f23dff3.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def get_structure(collection_ref, prefix=''):
    structure = f"{prefix}#{collection_ref.id} (collection)\n"

    docs = collection_ref.stream()
    for doc in docs:
        structure += f"{prefix}|- {doc.id} (document)\n"

        # Print fields
        data = doc.to_dict()
        for field in data:
            structure += f"{prefix}|  |- {field} (field)\n"

        # Check for sub-collections
        sub_collections = list(doc.reference.collections())
        for sub_collection in sub_collections:
            structure += get_structure(sub_collection, f"{prefix}|  ")

    return structure

def main():
    top_level_collections = db.collections()
    full_structure = ''

    for collection in top_level_collections:
        full_structure += get_structure(collection)

    print(full_structure)

if __name__ == '__main__':
    main()
