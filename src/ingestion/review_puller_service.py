import requests
import json
from datetime import datetime, timedelta
# from kafka import KafkaProducer # Assuming Kafka is installed: pip install kafka-python

class AmazonReviewPuller:
    def __init__(self, api_endpoint, access_key, secret_key, region, kafka_bootstrap_servers='localhost:9092'):
        self.api_endpoint = api_endpoint
        self.headers = {
            "X-Amazon-Access-Key": access_key,
            "X-Amazon-Secret-Key": secret_key, # In a real system, these would be managed securely (e.g., AWS Secrets Manager)
            "Content-Type": "application/json"
        }
        self.region = region
        # self.producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers,
        #                              value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'))

    def _authenticate(self):
        # Placeholder for actual Amazon authentication logic (e.g., LWA - Login With Amazon)
        # This would typically involve exchanging credentials for a temporary access token.
        # For simplicity, we assume pre-configured keys in this sprint.
        print("Authenticating with Amazon API...")
        # In a real scenario, this would return an actual token or raise an exception
        return True # Assume success for pseudocode

    def fetch_recent_reviews(self, last_pulled_timestamp=None):
        """
        Fetches recent reviews from the Amazon API.
        :param last_pulled_timestamp: ISO formatted string of the last time reviews were pulled.
        """
        if not self._authenticate():
            print("Authentication failed. Cannot fetch reviews.")
            return []

        params = {"pageSize": 100, "sortOrder": "DESC", "sortBy": "REVIEW_DATE"}
        if last_pulled_timestamp:
            params["startDate"] = last_pulled_timestamp # Fetch reviews since this date

        all_reviews = []
        next_token = None
        attempt_count = 0
        max_attempts = 3

        while attempt_count < max_attempts:
            if next_token:
                params["nextToken"] = next_token

            try:
                response = requests.get(
                    f"{self.api_endpoint}/reviews",
                    headers=self.headers,
                    params=params,
                    timeout=30 # 30 seconds timeout
                )
                response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
                data = response.json()

                reviews = data.get("reviews", [])
                all_reviews.extend(reviews)
                print(f"Fetched {len(reviews)} reviews. Total: {len(all_reviews)}")

                next_token = data.get("nextToken")
                if not next_token or not reviews: # No more pages or no reviews in the current page
                    break

                attempt_count = 0 # Reset attempt count on successful page fetch

            except requests.exceptions.HTTPError as e:
                print(f"HTTP Error fetching reviews (Status {e.response.status_code}): {e}")
                if e.response.status_code == 429: # Too Many Requests
                    print("Rate limit hit. Retrying after some time...")
                    # Implement exponential backoff here
                    import time
                    time.sleep(2 ** attempt_count)
                    attempt_count += 1
                    continue
                break # For other HTTP errors, break.
            except requests.exceptions.RequestException as e:
                print(f"Network or request error fetching reviews: {e}")
                break
            except json.JSONDecodeError:
                print("Error decoding JSON response from Amazon API.")
                break
            except Exception as e:
                print(f"An unexpected error occurred during review fetch: {e}")
                break
        
        if attempt_count >= max_attempts:
            print(f"Failed to fetch reviews after {max_attempts} attempts due to repeated errors.")

        return all_reviews

    def publish_review_to_queue(self, review_data):
        """
        Publishes a raw review dictionary to the Kafka 'review-raw' topic.
        """
        try:
            # self.producer.send('review-raw', review_data)
            # self.producer.flush() # Ensure message is sent immediately for demonstration
            print(f"Published review {review_data.get('externalReviewId')} to 'review-raw' topic.")
        except Exception as e:
            print(f"Error publishing review to Kafka: {e}")

    # Example of how this might be used in a scheduled job:
    # if __name__ == "__main__":
    #     # Placeholder for environment variables or secure configuration
    #     API_ENDPOINT = "https://sellingpartnerapi-na.amazon.com"
    #     ACCESS_KEY = "YOUR_AMAZON_ACCESS_KEY"
    #     SECRET_KEY = "YOUR_AMAZON_SECRET_KEY"
    #     REGION = "us-east-1"
    #
    #     puller = AmazonReviewPuller(API_ENDPOINT, ACCESS_KEY, SECRET_KEY, REGION)
    #
    #     # In a real system, 'last_pulled_timestamp' would be stored in a database
    #     # or a cache to prevent reprocessing old reviews.
    #     # For this example, let's fetch reviews from the last 24 hours.
    #     one_day_ago = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
    #     recent_reviews = puller.fetch_recent_reviews(last_pulled_timestamp=one_day_ago)
    #
    #     for review in recent_reviews:
    #         puller.publish_review_to_queue(review)
    #
    #     print(f"Finished pulling and publishing {len(recent_reviews)} reviews.")
