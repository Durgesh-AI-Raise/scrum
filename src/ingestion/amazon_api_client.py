import requests
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field

@dataclass
class Review:
    reviewId: str
    productId: str
    reviewerId: str
    reviewerName: str
    rating: int # 1-5
    title: str
    content: str
    reviewDate: datetime # Original review date
    ingestionTimestamp: datetime = field(default_factory=datetime.now)
    isVerifiedPurchase: bool = False
    reviewerAccountCreationDate: datetime = None

class AmazonAPIClient:
    def __init__(self, base_url, api_key, max_retries=3, initial_delay=1):
        self.base_url = base_url
        self.api_key = api_key
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def _make_request(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except requests.exceptions.HTTPError as e:
                if 429 == response.status_code:  # Too Many Requests
                    delay = self.initial_delay * (2 ** retries)
                    print(f"Rate limit hit. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    retries += 1
                elif 400 <= response.status_code < 500:
                    print(f"Client error {response.status_code}: {e}")
                    raise
                else:  # Server errors, or other HTTP errors
                    print(f"Server error {response.status_code}: {e}. Retrying...")
                    time.sleep(self.initial_delay)
                    retries += 1
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}. Retrying...")
                time.sleep(self.initial_delay)
                retries += 1
        raise Exception(f"Failed to make request to {url} after {self.max_retries} retries.")

    def fetch_new_reviews(self, product_id=None, since: datetime = None, limit=100):
        """
        Fetches new reviews from the Amazon API.
        This assumes an API endpoint that can filter by product_id and a 'since' timestamp.
        """
        endpoint = "reviews"
        params = {"limit": limit}
        if product_id:
            params["productId"] = product_id
        if since:
            params["since"] = since.isoformat() # Use ISO format for timestamp

        response_data = self._make_request(endpoint, params)
        return response_data.get("reviews", []) # Assuming the API returns a 'reviews' key
