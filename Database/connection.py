from pymongo import MongoClient

def get_database():

    client = MongoClient("mongodb://localhost:27017/")
    db = client["BiasZero"]
    return db

def get_collection(collection_name: str):
    db = get_database()
    collection = db[collection_name]
    return collection


    
if __name__ == "__main__":
    db = get_database()
    if db is not None:
        print("Database Name:", db.name) 
    else:
        print("No Database found")
    col = get_collection("Login")
    if col is not None:
        print("Collection name:",col.name)
    else:
        print("No Collection")