import datetime
import uuid

# --- Mock Database Client for local testing and pseudocode ---
class MockCollection:
    def __init__(self, collection_name=""):
        self.collection_name = collection_name
        self.data = [] # Stores dictionary documents
        print(f"MockCollection '{self.collection_name}' initialized.")

    def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = str(uuid.uuid4())
        self.data.append(doc)
        print(f"Inserted into '{self.collection_name}': {doc['_id']}")
        return {"inserted_id": doc["_id"]}

    def find_one(self, query):
        for doc in self.data:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc
        return None

    def find(self, query={}):
        results = [doc for doc in self.data if all(doc.get(k) == v for k,v in query.items())]
        # Return a copy to allow further operations like sort without modifying original
        return list(results)

    def update_one(self, query, update_doc, upsert=False):
        for i, doc in enumerate(self.data):
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                # Apply $set operations
                if "$set" in update_doc:
                    for set_k, set_v in update_doc["$set"].items():
                        # Handle nested updates (basic)
                        if '.' in set_k:
                            keys = set_k.split('.')
                            current_level = self.data[i]
                            for j, key in enumerate(keys):
                                if j == len(keys) - 1:
                                    current_level[key] = set_v
                                else:
                                    current_level = current_level.setdefault(key, {})
                        else:
                            self.data[i][set_k] = set_v
                # Apply $push operations (for arrays)
                if "$push" in update_doc:
                    for push_k, push_v in update_doc["$push"].items():
                        self.data[i].setdefault(push_k, []).append(push_v)
                # Apply $inc operations (for numbers)
                if "$inc" in update_doc:
                    for inc_k, inc_v in update_doc["$inc"].items():
                        # Basic handling of nested increments
                        if '.' in inc_k:
                            keys = inc_k.split('.')
                            current_level = self.data[i]
                            for j, key in enumerate(keys):
                                if j == len(keys) - 1:
                                    current_level[key] = current_level.get(key, 0) + inc_v
                                else:
                                    current_level = current_level.setdefault(key, {})
                        else:
                            self.data[i][inc_k] = self.data[i].get(inc_k, 0) + inc_v
                print(f"Updated in '{self.collection_name}': {doc['_id']}")
                return {"modified_count": 1}
        
        # If no match and upsert is True, insert the document
        if upsert:
            new_doc = query.copy()
            if "$set" in update_doc:
                new_doc.update(update_doc["$set"])
            if "$setOnInsert" in update_doc:
                new_doc.update(update_doc["$setOnInsert"])
            if "_id" not in new_doc:
                new_doc["_id"] = str(uuid.uuid4())
            self.insert_one(new_doc)
            print(f"Upserted (inserted) into '{self.collection_name}': {new_doc['_id']}")
            return {"modified_count": 1, "upserted": True}

        return {"modified_count": 0}

class MockDbClient:
    def __init__(self):
        self.reviews = MockCollection("reviews")
        self.products = MockCollection("products")
        self.reviewers = MockCollection("reviewers")
        print("MockDbClient initialized with collections: reviews, products, reviewers")
