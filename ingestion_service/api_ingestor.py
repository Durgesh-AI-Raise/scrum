# ingestion_service/api_ingestor.py

import requests
import json
from kafka import KafkaProducer
import datetime

# Configuration
AMAZON_API_ENDPOINT = "https://api.amazon.com/reviews/new" # Placeholder - replace with actual Amazon API endpoint
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC_REVIEWS = "amazon_reviews_raw"

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def fetch_new_reviews():
    """
    Fetches new review data from Amazon API and publishes to Kafka.
    """
    try:
        # In a real scenario, this would involve authentication and specific API parameters
        # For MVP, simulating a GET request
        response = requests.get(AMAZON_API_ENDPOINT, params={"since": (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat()})
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        reviews_data = response.json()

        for review_raw in reviews_data.get('reviews', []):
            # Basic transformation to Review model structure
            review = {
                "reviewId": review_raw.get("id"),
                "productId": review_raw.get("product_id"),
                "reviewerId": review_raw.get("reviewer_id"),
                "rating": review_raw.get("rating"),
                "reviewTitle": review_raw.get("title"),
                "reviewText": review_raw.get("text"),
                "reviewDate": review_raw.get("date"), # ISO format assumed
                "verifiedPurchase": review_raw.get("verified_purchase", False),
                "helpfulVotes": review_raw.get("helpful_votes", 0),
                "productCategory": review_raw.get("product_category"),
                "productBrand": review_raw.get("product_brand"),
                "reviewSource": "Amazon_API",
                "ingestionTimestamp": datetime.datetime.now().isoformat()
            }
            print(f"Ingesting real-time review: {review['reviewId']}")
            producer.send(KAFKA_TOPIC_REVIEWS, review)
        producer.flush()
        print(f"Successfully ingested {len(reviews_data.get('reviews', []))} new reviews.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching reviews from Amazon API: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during API ingestion: {e}")

if __name__ == "__main__":
    # This function would typically be run periodically by a scheduler (e.g., cron, Kubernetes CronJob)
    fetch_new_reviews()
