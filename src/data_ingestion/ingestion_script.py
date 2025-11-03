import json
from pymongo import MongoClient
import os

def ingest_review_data(file_path, mongo_uri, db_name, collection_name):
    """
    Ingests review data (review_text, ratings, dates) from a JSON file into MongoDB.
    """
    try:
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]
        print(f"Connected to MongoDB: {mongo_uri}, Database: {db_name}, Collection: {collection_name}")

        processed_count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    review_record = {
                        "review_id": data.get("review_id"),
                        "review_text": data.get("review_text"),
                        "overall_rating": data.get("overall_rating"), # Keep as is, validation later
                        "review_date": data.get("review_date")
                    }
                    # Only insert if review_id is present and not None
                    if review_record["review_id"]:
                        # Use upsert to handle updates if review_id already exists
                        collection.update_one(
                            {"review_id": review_record["review_id"]},
                            {"$set": review_record},
                            upsert=True
                        )
                        processed_count += 1
                    else:
                        print(f"Warning: Skipping record due to missing review_id: {data}")
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in line: {line.strip()} - {e}")
                except Exception as e:
                    print(f"An unexpected error occurred while processing line: {line.strip()} - {e}")
        client.close()
        print(f"Ingestion complete for {file_path}. Processed {processed_count} records.")
    except Exception as e:
        print(f"Failed to connect to MongoDB or an error occurred during ingestion setup: {e}")

if __name__ == "__main__":
    # Environment variables for sensitive information and configuration
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME = os.getenv("DB_NAME", "amazon_reviews")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "reviews")
    SAMPLE_DATA_FILE = "sample_reviews_initial.json" # Relative path

    # Create a dummy sample_reviews_initial.json for demonstration
    # In a real scenario, this file would be provided or fetched from S3.
    if not os.path.exists(SAMPLE_DATA_FILE):
        print(f"Creating dummy sample data file: {SAMPLE_DATA_FILE}")
        dummy_data = [
            {"review_id": "R1", "review_text": "Great product!", "overall_rating": 5, "review_date": "2023-01-01"},
            {"review_id": "R2", "review_text": "Not bad.", "overall_rating": 3, "review_date": "2023-01-02"},
            {"review_id": "R3", "review_text": "Awesome!", "overall_rating": 5, "review_date": "2023-01-03"}
        ]
        with open(SAMPLE_DATA_FILE, 'w', encoding='utf-8') as f:
            for item in dummy_data:
                f.write(json.dumps(item) + '\n')

    print(f"Starting ingestion process using data from {SAMPLE_DATA_FILE}...")
    ingest_review_data(SAMPLE_DATA_FILE, MONGO_URI, DB_NAME, COLLECTION_NAME)
