from datetime import datetime
from services.data_ingestion.mock_db import mock_db

class ReviewFlaggingService:
    def __init__(self):
        self.short_review_min_words = 10
        self.suspicious_keywords = ["buy now", "discount code", "amazing offer", "deal of the day"]

    def flag_review(self, review):
        flags = []

        # Rule 1: Short 5-star review
        if review['rating'] == 5 and len(review['review_content'].split()) < self.short_review_min_words:
            flags.append("short_5_star_review")

        # Rule 2: Keyword stuffing
        review_content_lower = review['review_content'].lower()
        for keyword in self.suspicious_keywords:
            if keyword in review_content_lower:
                flags.append(f"keyword_stuffing: {keyword}")
                # For MVP, just add the first one found per review. Could be extended to list all.
                break 

        if flags:
            flagged_data = {
                "review_id": review['review_id'],
                "flag_reason": flags,
                "flag_timestamp": datetime.now()
            }
            mock_db.add_flagged_review(flagged_data)
            return True
        return False

review_flagging_service = ReviewFlaggingService()