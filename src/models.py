class Review:
    def __init__(self, review_id: str, text: str, reviewer_id: str):
        self.review_id = review_id
        self.text = text
        self.reviewer_id = reviewer_id

class FlaggedReview:
    def __init__(self, review_id: str, flag_type: str, timestamp: str, confidence_score: float = 0.0):
        self.review_id = review_id
        self.flag_type = flag_type
        self.timestamp = timestamp
        self.confidence_score = confidence_score

    def to_dict(self):
        return {
            "review_id": self.review_id,
            "flag_type": self.flag_type,
            "timestamp": self.timestamp,
            "confidence_score": self.confidence_score
        }