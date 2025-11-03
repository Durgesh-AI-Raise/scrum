
import boto3
import json
import datetime
import random

kinesis_client = boto3.client('kinesis', region_name='us-east-1')
STREAM_NAME = 'amazon-reviews-stream'

def generate_mock_review():
    review_id = f"R{random.randint(10000, 99999)}"
    product_asin = f"B{random.randint(100000000, 999999999)}"
    reviewer_id = f"A{random.randint(10000000000000, 99999999999999)}"
    review_text = random.choice([
        "This product is absolutely amazing and worth every penny. Highly recommend!",
        "Beware! This product broke after a week. Very disappointed.",
        "I received this gifted product for my honest opinion, and it's great.",
        "Paid review, but seriously, it's good.",
        "CompetitorX has better options at this price point.",
        "Decent product, nothing special.",
        "Received this for free in exchange for a review.",
        "Love it, a must-buy!",
    ])
    star_rating = random.randint(1, 5)
    review_date = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds') + "Z"
    country_code = random.choice(["US", "UK", "DE", "JP"])
    review_title = random.choice(["Fantastic!", "Terrible!", "Mixed Feelings", "Worth It", "Waste of Money"])
    
    return {
        "review_id": review_id,
        "product_asin": product_asin,
        "reviewer_id": reviewer_id,
        "review_text": review_text,
        "star_rating": star_rating,
        "review_date": review_date,
        "country_code": country_code,
        "review_title": review_title
    }

def send_review_to_kinesis(review_data):
    partition_key = review_data['reviewer_id'] # Use reviewer_id for even distribution
    payload = json.dumps(review_data)
    try:
        response = kinesis_client.put_record(
            StreamName=STREAM_NAME,
            Data=payload,
            PartitionKey=partition_key
        )
        print(f"Sent review {review_data['review_id']} to Kinesis. Sequence Number: {response['SequenceNumber']}")
    except Exception as e:
        print(f"Error sending review {review_data['review_id']} to Kinesis: {e}")

# Example Usage (can be put in a loop to continuously send data):
# if __name__ == "__main__":
#     for _ in range(5):
#         new_review = generate_mock_review()
#         send_review_to_kinesis(new_review)
#         import time
#         time.sleep(1)

