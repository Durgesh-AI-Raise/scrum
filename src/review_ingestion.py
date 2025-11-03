from src.models import Review

class ReviewIngestionService:
    def __init__(self):
        # Simulate a data source with an in-memory list of reviews
        self._reviews = [
            Review(review_id="R001", text="This product is absolutely amazing! I love it, love it, love it! Highly recommend it to everyone.", reviewer_id="U101"),
            Review(review_id="R002", text="It's okay. Nothing special. Just a product.", reviewer_id="U102"),
            Review(review_id="R003", text="Terrible experience. The worst, worst, worst product I've ever bought. Complete waste of money.", reviewer_id="U103"),
            Review(review_id="R004", text="A decent product, performs as expected.", reviewer_id="U104"),
            Review(review_id="R005", text="Amazing! Fantastic! Superb! Excellent! Top-notch! A+++", reviewer_id="U105"), # Keyword stuffing candidate
            Review(review_id="R006", text="This is an absolutely fantastic product. The quality is exceptional and I highly recommend it.", reviewer_id="U106"), # High positive sentiment
            Review(review_id="R007", text="I am utterly disappointed with this product. It broke immediately and was a complete letdown.", reviewer_id="U107") # High negative sentiment
        ]

    def get_all_reviews(self) -> list[Review]:
        return self._reviews

    def get_review_by_id(self, review_id: str) -> Review | None:
        for review in self._reviews:
            if review.review_id == review_id:
                return review
        return None