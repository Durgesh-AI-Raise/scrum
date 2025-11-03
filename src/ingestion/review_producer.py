import json
import time
import random
from datetime import datetime
import boto3

# Configuration for Kinesis Stream (to be set via environment variables or configuration management)
KINESIS_STREAM_NAME = "RawReviewsStream" 
AWS_REGION = "us-east-1"

def generate_mock_review():
    """Generates a mock review dictionary."""
    review_id = f"R{random.randint(100000, 999999)}"
    product_id = f"P{random.randint(1000, 9999)}"
    reviewer_id = f"U{random.randint(10000, 99999)}"
    stars = random.randint(1, 5)
    review_titles = ["Great Product!", "Highly Recommended", "Disappointed", "Good Value", "Works as expected"]
    review_texts = [
        "This product is amazing, I love it so much. The features are great and it's very easy to use.",
        "I had high hopes for this, but it fell short. The quality is not what I expected.",
        "Fantastic product for the price. Definitely worth buying if you're on a budget.",
        "It's okay, nothing special. Does the job, but there are better alternatives out there.",
        "My experience was terrible. I would not recommend this to anyone. Stay away!"
    ]
    countries = ["US", "CA", "GB", "DE"]
    languages = ["en"]
    source_urls = [f"https://amazon.com/dp/{product_id}"]

    review = {
        "review_id": review_id,
        "product_id": product_id,
        "reviewer_id": reviewer_id,
        "stars": stars,
        "review_title": random.choice(review_titles),
        "review_text": random.choice(review_texts),
        "review_date": datetime.now().strftime("%Y-%m-%d"),
        "country": random.choice(countries),
        "language": random.choice(languages),
        "source_url": random.choice(source_urls),
        "extracted_at": datetime.utcnow().isoformat(timespec='milliseconds') + "Z"
    }
    return review

def put_record_to_kinesis(stream_name, record, partition_key, region=AWS_REGION):
    """Puts a single record into a Kinesis Data Stream."""
    client = boto3.client('kinesis', region_name=region)
    try:
        response = client.put_record(
            StreamName=stream_name,
            Data=json.dumps(record),
            PartitionKey=partition_key
        )
        print(f"Successfully sent review {record.get('review_id', 'N/A')} to Kinesis. SequenceNumber: {response['SequenceNumber']}")
        return response
    except Exception as e:
        print(f"Error sending record to Kinesis: {e}")
        # Implement retry logic or dead-letter queueing if necessary
        raise

def main():
    print(f"Starting Kinesis producer for stream: {KINESIS_STREAM_NAME}")
    while True:
        review_data = generate_mock_review()
        # Use product_id or reviewer_id as partition key for better distribution/co-location
        partition_key = review_data["product_id"] 
        
        try:
            put_record_to_kinesis(KINESIS_STREAM_NAME, review_data, partition_key)
        except Exception as e:
            print(f"Failed to put record: {e}")
            # Decide on error handling: continue, break, specific retry logic
        
        time.sleep(random.uniform(0.1, 1.0)) # Simulate varying arrival times

if __name__ == "__main__":
    main()
