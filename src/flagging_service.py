import sqlite3
from datetime import datetime
from src.models import FlaggedReview, Review
from src.linguistic_detection import LinguisticDetector

class FlaggedReviewRepository:
    def __init__(self, db_path="flagged_reviews.db"):
        self.db_path = db_path
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flagged_reviews (
                review_id TEXT PRIMARY KEY,
                flag_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                confidence_score REAL
            )
        ''')
        conn.commit()
        conn.close()

    def add_flagged_review(self, flagged_review: FlaggedReview):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()        
        cursor.execute('''
            INSERT OR REPLACE INTO flagged_reviews (review_id, flag_type, timestamp, confidence_score)
            VALUES (?, ?, ?, ?)
        ''', (flagged_review.review_id, flagged_review.flag_type, flagged_review.timestamp, flagged_review.confidence_score))
        conn.commit()
        conn.close()

    def get_all_flagged_reviews(self) -> list[FlaggedReview]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT review_id, flag_type, timestamp, confidence_score FROM flagged_reviews")
        rows = cursor.fetchall()
        conn.close()
        return [FlaggedReview(row[0], row[1], row[2], row[3]) for row in rows]

    def get_flagged_review_by_id(self, review_id: str) -> FlaggedReview | None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT review_id, flag_type, timestamp, confidence_score FROM flagged_reviews WHERE review_id = ?", (review_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return FlaggedReview(row[0], row[1], row[2], row[3])
        return None

class FlaggingService:
    def __init__(self, linguistic_detector: LinguisticDetector, repository: FlaggedReviewRepository):
        self.detector = linguistic_detector
        self.repository = repository

    def flag_review(self, review: Review) -> FlaggedReview | None:
        is_keyword_stuffing, ks_confidence = self.detector.detect_keyword_stuffing(review.text)
        is_extreme_sentiment, es_confidence = self.detector.detect_extreme_sentiment(review.text)

        if is_keyword_stuffing:
            flagged_review = FlaggedReview(
                review_id=review.review_id,
                flag_type="keyword_stuffing",
                timestamp=datetime.now().isoformat(),
                confidence_score=ks_confidence
            )
            self.repository.add_flagged_review(flagged_review)
            return flagged_review
        elif is_extreme_sentiment:
            flagged_review = FlaggedReview(
                review_id=review.review_id,
                flag_type="extreme_sentiment",
                timestamp=datetime.now().isoformat(),
                confidence_score=es_confidence
            )
            self.repository.add_flagged_review(flagged_review)
            return flagged_review
        return None

    def flag_all_reviews(self, reviews: list[Review]) -> list[FlaggedReview]:
        flagged_reviews = []
        for review in reviews:
            flag = self.flag_review(review)
            if flag:
                flagged_reviews.append(flag)
        return flagged_reviews
