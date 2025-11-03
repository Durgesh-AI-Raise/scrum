import uuid
import time

class ProcessedReview:
    """
    Represents a processed review with cleaned text and abuse flags.
    This model would be stored in a NoSQL database.
    """
    def __init__(self, original_review_id: str, product_id: str, reviewer_id: str, 
                 rating: int, timestamp: int, cleaned_text: str):
        self.processed_review_id = str(uuid.uuid4())  # Generate a unique ID for the processed review
        self.original_review_id = original_review_id
        self.product_id = product_id
        self.reviewer_id = reviewer_id
        self.rating = rating
        self.timestamp = timestamp
        self.cleaned_text = cleaned_text
        self.sentiment_score = None  # To be populated by future sentiment analysis modules
        self.abuse_flags = []        # List of flags detected for this review
        self.analyst_status = {
            "status": "pending",  # Initial status
            "analyst_id": None,
            "action_taken": None,
            "last_updated": None
        }

    def add_flag(self, flag_type: str, severity: str, reason: str):
        """
        Adds an abuse flag to the review.
        """
        self.abuse_flags.append({
            "flag_type": flag_type,
            "detection_time": int(time.time() * 1000), # Current epoch milliseconds
            "severity": severity,
            "reason": reason
        })

    def update_analyst_status(self, status: str, analyst_id: str = None, action_taken: str = None):
        """
        Updates the analyst review status for the review.
        """
        self.analyst_status = {
            "status": status,
            "analyst_id": analyst_id,
            "action_taken": action_taken,
            "last_updated": int(time.time() * 1000)
        }

    def to_dict(self):
        """
        Converts the ProcessedReview object to a dictionary for database storage.
        """
        return {
            "processed_review_id": self.processed_review_id,
            "original_review_id": self.original_review_id,
            "product_id": self.product_id,
            "reviewer_id": self.reviewer_id,
            "rating": self.rating,
            "timestamp": self.timestamp,
            "cleaned_text": self.cleaned_text,
            "sentiment_score": self.sentiment_score,
            "abuse_flags": self.abuse_flags,
            "analyst_status": self.analyst_status
        }

class ReviewerProfile:
    """
    Represents a reviewer's aggregated profile and associated abuse flags.
    This model would be stored in a NoSQL database.
    """
    def __init__(self, reviewer_id: str):
        self.reviewer_id = reviewer_id
        self.total_reviews = 0
        self.average_rating = 0.0
        self.brands_reviewed = []       # List of unique brand IDs reviewed by this user
        self.product_ids_reviewed = []  # List of unique product IDs reviewed by this user
        self.review_timestamps = []     # Sorted list of all review timestamps by this user
        self.abuse_flags = []
        self.analyst_status = {
            "status": "pending",
            "analyst_id": None,
            "action_taken": None,
            "last_updated": None
        }

    def update_profile(self, new_review_data: dict):
        """
        Updates the reviewer's profile based on a new review.
        """
        self.total_reviews += 1
        
        current_sum_ratings = self.average_rating * (self.total_reviews - 1)
        self.average_rating = (current_sum_ratings + new_review_data['rating']) / self.total_reviews

        product_id = new_review_data.get('product_id')
        if product_id and product_id not in self.product_ids_reviewed:
            self.product_ids_reviewed.append(product_id)

        # Assuming 'brand_id' might come in the review data or can be derived from product_id
        brand_id = new_review_data.get('brand_id') # Placeholder for now
        if brand_id and brand_id not in self.brands_reviewed:
            self.brands_reviewed.append(brand_id)

        timestamp = new_review_data.get('timestamp')
        if timestamp:
            self.review_timestamps.append(timestamp)
            self.review_timestamps.sort() # Keep timestamps sorted for temporal analysis

    def add_flag(self, flag_type: str, severity: str, reason: str):
        """
        Adds an abuse flag to the reviewer profile.
        """
        self.abuse_flags.append({
            "flag_type": flag_type,
            "detection_time": int(time.time() * 1000),
            "severity": severity,
            "reason": reason
        })

    def update_analyst_status(self, status: str, analyst_id: str = None, action_taken: str = None):
        """
        Updates the analyst review status for the reviewer profile.
        """
        self.analyst_status = {
            "status": status,
            "analyst_id": analyst_id,
            "action_taken": action_taken,
            "last_updated": int(time.time() * 1000)
        }

    def to_dict(self):
        """
        Converts the ReviewerProfile object to a dictionary for database storage.
        """
        return {
            "reviewer_id": self.reviewer_id,
            "total_reviews": self.total_reviews,
            "average_rating": self.average_rating,
            "brands_reviewed": self.brands_reviewed,
            "product_ids_reviewed": self.product_ids_reviewed,
            "review_timestamps": self.review_timestamps,
            "abuse_flags": self.abuse_flags,
            "analyst_status": self.analyst_status
        }
