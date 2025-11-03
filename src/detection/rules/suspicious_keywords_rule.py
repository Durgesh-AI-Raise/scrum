import re
from typing import List, Tuple, Optional

from src.data_models.review_model import Review
from src.detection.rules_engine import Rule

class SuspiciousKeywordsRule(Rule):
    def __init__(self, rule_id: str = "SUSPICIOUS_KEYWORDS_RULE", description: str = "Detects reviews containing suspicious keyword patterns."):
        super().__init__(rule_id, description)
        self.suspicious_keywords = ["free gift", "discount code", "promo code", "earn money", "cashback", "amazon voucher"]

    def evaluate(self, review: Review) -> Tuple[bool, Optional[str]]:
        review_text_lower = review.reviewText.lower()
        triggered_keywords = []
        for keyword in self.suspicious_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', review_text_lower):
                triggered_keywords.append(keyword)

        if triggered_keywords:
            reason = f"Review contains suspicious keywords: {', '.join(triggered_keywords)}"
            review.detectionResults.suspiciousKeywords = True
            return True, reason
        return False, None

# Example Usage (for testing purposes, not part of the deployed code directly)
# if __name__ == "__main__":
#     from datetime import datetime
#     from src.data_models.review_model import Review, ReviewMetadata
#
#     rule = SuspiciousKeywordsRule()
#
#     # Test case 1: Contains suspicious keywords
#     review1 = Review(
#         reviewId="R001", productId="P101", reviewerId="U201",
#         reviewText="This product is good, and I got a free gift with my purchase!",
#         rating=4, timestamp=datetime.utcnow()
#     )
#     triggered, reason = rule.evaluate(review1)
#     print(f"Review 1 Triggered: {triggered}, Reason: {reason}, DetectionResults: {review1.detectionResults.suspiciousKeywords}")
#     assert triggered is True
#     assert "free gift" in reason
#     assert review1.detectionResults.suspiciousKeywords is True
#
#     # Test case 2: Contains another suspicious keyword
#     review2 = Review(
#         reviewId="R002", productId="P102", reviewerId="U202",
#         reviewText="I used a discount code for this. Great value.",
#         rating=5, timestamp=datetime.utcnow()
#     )
#     triggered, reason = rule.evaluate(review2)
#     print(f"Review 2 Triggered: {triggered}, Reason: {reason}, DetectionResults: {review2.detectionResults.suspiciousKeywords}")
#     assert triggered is True
#     assert "discount code" in reason
#     assert review2.detectionResults.suspiciousKeywords is True
#
#     # Test case 3: No suspicious keywords
#     review3 = Review(
#         reviewId="R003", productId="P103", reviewerId="U203",
#         reviewText="Very happy with my order. Fast shipping.",
#         rating=5, timestamp=datetime.utcnow()
#     )
#     triggered, reason = rule.evaluate(review3)
#     print(f"Review 3 Triggered: {triggered}, Reason: {reason}, DetectionResults: {review3.detectionResults.suspiciousKeywords}")
#     assert triggered is False
#     assert reason is None
#     assert review3.detectionResults.suspiciousKeywords is False
#
#     # Test case 4: Case insensitive
#     review4 = Review(
#         reviewId="R004", productId="P104", reviewerId="U204",
#         reviewText="Got a FREE GIFT with this!",
#         rating=4, timestamp=datetime.utcnow()
#     )
#     triggered, reason = rule.evaluate(review4)
#     print(f"Review 4 Triggered: {triggered}, Reason: {reason}, DetectionResults: {review4.detectionResults.suspiciousKeywords}")
#     assert triggered is True
#     assert "free gift" in reason
#     assert review4.detectionResults.suspiciousKeywords is True
