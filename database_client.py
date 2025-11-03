from pymongo import MongoClient
from pymongo.errors import CollectionInvalid

class DatabaseClient:
    def __init__(self, db_uri: str, db_name: str):
        self.client = MongoClient(db_uri)
        self.db = self.client[db_name]
        self._ensure_collections_and_indexes()
        print(f"Connected to MongoDB database: {db_name}")

    def _ensure_collections_and_indexes(self):
        # Ensure collections exist and apply indexes
        collections = ["reviews", "products", "reviewers"]
        for col_name in collections:
            if col_name not in self.db.list_collection_names():
                self.db.create_collection(col_name)
                print(f"Collection '{col_name}' created.")

        # Create indexes for 'reviews' collection
        self.db.reviews.create_index("review_id", unique=True)
        self.db.reviews.create_index("product_id")
        self.db.reviews.create_index("reviewer_id")
        self.db.reviews.create_index("status")
        self.db.reviews.create_index([("review_date", -1)]) # For recent reviews

        # Create indexes for 'products' collection
        self.db.products.create_index("product_id", unique=True)
        self.db.products.create_index("status")

        # Create indexes for 'reviewers' collection
        self.db.reviewers.create_index("reviewer_id", unique=True)
        self.db.reviewers.create_index("status")
        print("MongoDB collections and indexes ensured.")

    def upsert_document(self, collection_name: str, query: dict, document: dict):
        """Inserts or updates a document."""
        collection = self.db[collection_name]
        result = collection.update_one(query, {"$set": document}, upsert=True)
        return result

    def find_document(self, collection_name: str, query: dict):
        """Finds a single document."""
        collection = self.db[collection_name]
        return collection.find_one(query)

    def find_documents(self, collection_name: str, query: dict, sort_by=None, limit=0):
        """Finds multiple documents."""
        collection = self.db[collection_name]
        cursor = collection.find(query)
        if sort_by:
            cursor = cursor.sort(sort_by)
        if limit > 0:
            cursor = cursor.limit(limit)
        return list(cursor)

    def update_document_status(self, collection_name: str, item_id_field: str, item_id: str, new_status: str, analyst_id: str = None, notes: str = None):
        """Updates the status of a document."""
        collection = self.db[collection_name]
        update_fields = {"status": new_status}
        if analyst_id:
            update_fields["last_updated_by_analyst"] = analyst_id
        if notes:
            update_fields["analyst_notes"] = notes
        result = collection.update_one({item_id_field: item_id}, {"$set": update_fields})
        return result

