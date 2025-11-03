# backend/similarity_detection_service.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from datetime import datetime
# Assuming models are in a directory one level up or properly managed in PYTHONPATH
from models import Review, FlaggedItem

class ReviewSimilarityDetector:
    def __init__(self, db_session_factory, similarity_threshold=0.8):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.corpus_reviews = [] # List of {'review_id': int, 'review_text': str}
        self.tfidf_matrix = None
        self.similarity_threshold = similarity_threshold
        self.db_session_factory = db_session_factory
        self.rebuild_corpus_needed = True # Flag to rebuild corpus if reviews change

    def _get_all_reviews_from_db(self, session):
        return session.query(Review).with_entities(Review.review_id, Review.review_text).all()

    def build_corpus(self, session=None):
        if not self.rebuild_corpus_needed and self.tfidf_matrix is not None:
            return

        local_session = None
        if session is None:
            local_session = self.db_session_factory()
            reviews_data = self._get_all_reviews_from_db(local_session)
        else:
            reviews_data = self._get_all_reviews_from_db(session)

        self.corpus_reviews = [{'review_id': r.review_id, 'review_text': r.review_text} for r in reviews_data]
        review_texts = [r['review_text'] for r in self.corpus_reviews]

        if review_texts:
            self.tfidf_matrix = self.vectorizer.fit_transform(review_texts)
        else:
            self.tfidf_matrix = None

        self.rebuild_corpus_needed = False
        if local_session:
            local_session.close()


    def detect_similar_reviews(self, new_review_id, new_review_text, session):
        self.build_corpus(session) # Ensure corpus is up-to-date

        if self.tfidf_matrix is None or not self.corpus_reviews:
            return [] # No existing reviews to compare against

        # Transform the new review text
        new_review_vec = self.vectorizer.transform([new_review_text])

        # Calculate cosine similarity with all existing reviews
        similarities = cosine_similarity(new_review_vec, self.tfidf_matrix).flatten()

        flagged_similarities = []
        for i, score in enumerate(similarities):
            # Ensure we don't compare a review with itself and that it meets the threshold
            if self.corpus_reviews[i]['review_id'] != new_review_id and score >= self.similarity_threshold:
                flagged_similarities.append({
                    'original_review_id': self.corpus_reviews[i]['review_id'],
                    'similarity_score': score,
                    'new_review_id': new_review_id
                })
        return flagged_similarities

    def flag_reviews_in_db(self, review_id_1, review_id_2, reason, details):
        session = self.db_session_factory()
        try:
            # Flag review_id_1
            existing_flag_1 = session.query(FlaggedItem).filter_by(
                item_type='review',
                item_id=review_id_1,
                reason=reason
            ).first()
            if not existing_flag_1:
                flagged_item_1 = FlaggedItem(
                    item_type='review',
                    item_id=review_id_1,
                    reason=reason,
                    details=details,
                    timestamp=datetime.utcnow()
                )
                session.add(flagged_item_1)
                review_1 = session.query(Review).filter_by(review_id=review_id_1).first()
                if review_1:
                    review_1.is_flagged = True
                    review_1.flagging_reason = reason # Consider appending if multiple reasons

            # Flag review_id_2
            existing_flag_2 = session.query(FlaggedItem).filter_by(
                item_type='review',
                item_id=review_id_2,
                reason=reason
            ).first()
            if not existing_flag_2:
                flagged_item_2 = FlaggedItem(
                    item_type='review',
                    item_id=review_id_2,
                    reason=reason,
                    details=details,
                    timestamp=datetime.utcnow()
                )
                session.add(flagged_item_2)
                review_2 = session.query(Review).filter_by(review_id=review_id_2).first()
                if review_2:
                    review_2.is_flagged = True
                    review_2.flagging_reason = reason # Consider appending if multiple reasons

            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()