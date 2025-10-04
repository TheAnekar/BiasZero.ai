from pymongo import MongoClient
from pymongo.errors import PyMongoError
from Database.connection import get_collection,get_database

def create_document(collection_name:str, data:dict):
    try:
        collection = get_collection(collection_name)
        result = collection.insert_one(data)
        print(f'Document Inserted into {collection_name} with id:{result.inserted_id}')
        return result.inserted_id
    except PyMongoError as e:
        print(f"Error Inserting into {collection_name}:{e}")
        return None

def read_document(collection_name: str,query : dict = None):
    try:
        collection = get_collection(collection_name)
        cursor = collection.find(query or {})
        result = list(cursor)
        print(f"Found {len(result)} documents in {collection_name}")
        return result
    except PyMongoError as e:
        print(f"Error In Finding Document from {collection_name}:{e}")
        return []
    
def update_document(collection_name: str, query: dict , new_values : dict):
    try:
        collection = get_collection(collection_name)
        result = collection.update_many(query,{"$set": new_values})
        print(f"Modified {result.modified_count} document(s) in '{collection_name}'")
        return result.modified_count
    except PyMongoError as e:
        print(f"Error In Updating Document In {collection_name}: {e}")
        return 0
    
def delete_document(collection_name: str,query: dict):
    try:
        collection = get_collection(collection_name)
        result = collection.delete_many(query)
        print(f"Deleted {result.deleted_count} document(s) from {collection_name}")
        return result.deleted_count
    except PyMongoError as e:
        print(f"Error in Deleting documents from {collection_name}:{e}")
        return 0
    