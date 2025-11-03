# src/detection_modules.py
import spacy
from datetime import datetime, timedelta
from collections import Counter
from typing import Optional, List, Dict, Any

# --- Data Models (for clarity in detection modules) ---
class LinguisticFlag:
    """Represents a flag detected by the linguistic pattern analysis."""
    def __init__(self, pattern: str, score: float, details: Dict[str, Any]):
        self.pattern = pattern
        self.score = score
        self.details = details

    def to_dict(self):
        return {"pattern": self.pattern, "score": self.score, "details": self.details}

class BehavioralFlag:
    """Represents a flag detected by the behavioral pattern analysis."""
    def __init__(self, pattern: str, score: float, details: Dict[str, Any]):
        self.pattern = pattern
        self.score = score
        self.details = details

    def to_dict(self):
        return {"pattern": self.pattern, "score": self.score, "details": self.details}

class UserReviewHistory:
    """Aggregated history of a user's reviews for behavioral analysis."""
    def __init__(self, user_id: str, account_creation_date: datetime, reviews: List[Dict[str, Any]]):
        self.user_id = user_id
        self.account_creation_date = account_creation_date
        # Ensure reviews are sorted by post_date for time-series analysis
        self.reviews = sorted(reviews, key=lambda r: r['post_date'])

# --- P0-1: Linguistic Pattern Detection ---
# Task 1.2 & 1.3: Linguistic Processing Pipeline & Detection Module

# Load a small English model for spaCy.
# If 'en_core_web_sm' is not found, a dummy NLP object is used to prevent errors
# in environments where the model is not downloaded, but spaCy is installed.
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("SpaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'.")
    # Using a dummy NLP object for execution within this environment if model is not present
    class DummyToken:
        def __init__(self, text, is_stop=False, is_punct=False, is_alpha=True, lemma=None):
            self.text = text
            self.is_stop = is_stop
            self.is_punct = is_punct
            self.is_alpha = is_alpha
            self.lemma_ = lemma if lemma else text.lower()
    class DummyNLP:
        def __call__(self, text):
            # Mimic basic spaCy doc for demo
            tokens = []
            # Simple stop words and punctuation check
            simple_stopwords = {"the", "a", "an", "is", "it", "and", "or"}
            for word in text.split():
                if word.lower() in simple_stopwords:
                    tokens.append(DummyToken(word, is_stop=True))
                elif not word.isalnum():
                    tokens.append(DummyToken(word, is_punct=True, is_alpha=False))
                else:
                    tokens.append(DummyToken(word))
            return tokens
    nlp = DummyNLP()


def preprocess_review_text(text: str) -> str:
    """
    Implements a text processing pipeline for linguistic analysis.
    Steps: lowercase, tokenization, stop word removal, lemmatization.
    (Corresponds to Task 1.2)
    """
    text = text.lower()
    doc = nlp(text)
    processed_tokens = []
    for token in doc:
        # Basic filtering for demo. Real-world might use more refined logic.
        if not token.is_stop and not token.is_punct and token.is_alpha:
            processed_tokens.append(token.lemma_)
    return " ".join(processed_tokens)

def detect_linguistic_patterns(raw_text: str) -> List[LinguisticFlag]:
    """
    Detects suspicious linguistic patterns in review text based on defined rules.
    (Corresponds to Task 1.3 & 1.4)
    """
    flags = []
    processed_text = preprocess_review_text(raw_text)

    # Rule 1: Excessive punctuation (e.g., more than 5 exclamation marks)
    # Task 1.4: Define Initial Suspicious Linguistic Patterns/Rules
    if raw_text.count('!') > 5:
        flags.append(LinguisticFlag(
            pattern="excessive_punctuation",
            score=0.6,
            details={"char": "!", "count": raw_text.count('!')}
        ))

    # Rule 2: Keyword stuffing (example: "amazing" used too often)
    # Task 1.4: Define Initial Suspicious Linguistic Patterns/Rules
    target_keyword = "amazing"
    if target_keyword in processed_text:
        keyword_count = processed_text.count(target_keyword)
        total_words = len(processed_text.split())
        if total_words > 0 and (keyword_count / total_words) > 0.05: # Threshold: >5% density
            flags.append(LinguisticFlag(
                pattern="keyword_stuffing",
                score=0.75,
                details={"keyword": target_keyword, "density": round(keyword_count / total_words, 2)}
            ))

    # Rule 3: Very short, generic positive reviews (simple check)
    # Task 1.4: Define Initial Suspicious Linguistic Patterns/Rules
    if len(raw_text.split()) < 10 and any(phrase in raw_text.lower() for phrase in ["great product", "love it", "works well"]):
        flags.append(LinguisticFlag(
            pattern="generic_short_praise",
            score=0.5,
            details={"length": len(raw_text.split()), "matched_phrases": ["great product", "love it", "works well"]}
        ))

    return flags

# --- P0-2: Behavioral Pattern Detection ---
# Task 2.3 & 2.4: Behavioral Detection Module

def detect_behavioral_patterns(history: UserReviewHistory, current_review_date: datetime) -> List[BehavioralFlag]:
    """
    Detects suspicious reviewer behavioral patterns based on user review history.
    (Corresponds to Task 2.3 & 2.4)
    """
    flags = []
    total_reviews = len(history.reviews)
    if total_reviews == 0:
        return flags

    # Rule 1: New account, high frequency of reviews
    # Task 2.4: Define Initial Suspicious Behavioral Rules/Thresholds
    days_since_creation = (current_review_date - history.account_creation_date).days
    if days_since_creation <= 7 and total_reviews > 5: # Threshold: >5 reviews in 7 days
        flags.append(BehavioralFlag(
            pattern="new_account_high_frequency",
            score=0.8,
            details={"days_old": days_since_creation, "review_count": total_reviews}
        ))

    # Rule 2: Extreme rating bias (e.g., only 1-star or 5-star reviews)
    # Task 2.4: Define Initial Suspicious Behavioral Rules/Thresholds
    if total_reviews >= 3: # Need a few reviews to detect a pattern
        ratings = [r['rating'] for r in history.reviews]
        one_star_count = ratings.count(1)
        five_star_count = ratings.count(5)
        if (one_star_count / total_reviews) > 0.9 or (five_star_count / total_reviews) > 0.9: # Threshold: >90% extreme ratings
            flags.append(BehavioralFlag(
                pattern="extreme_rating_bias",
                score=0.9,
                details={"1_star_percent": round(one_star_count / total_reviews * 100, 1),
                         "5_star_percent": round(five_star_count / total_reviews * 100, 1)}
            ))

    # Rule 3: Reviews only one product type (using simplified 'category')
    # Task 2.4: Define Initial Suspicious Behavioral Rules/Thresholds
    if total_reviews >= 3:
        categories = [r['product_category'] for r in history.reviews if 'product_category' in r]
        if categories:
            category_counts = Counter(categories)
            most_common_category, count = category_counts.most_common(1)[0]
            if (count / total_reviews) > 0.8: # Threshold: >80% in one category
                flags.append(BehavioralFlag(
                    pattern="single_category_focus",
                    score=0.6,
                    details={"category": most_common_category, "percentage": round(count / total_reviews * 100, 1)}
                ))

    return flags

# --- P0-4: Integrate Linguistic & Behavioral Flagging into Combined Risk Score ---
# Task 4.4: Combined Risk Score Logic

def calculate_combined_risk_score(linguistic_flags: List[LinguisticFlag], behavioral_flags: List[BehavioralFlag]) -> float:
    """
    Calculates a combined risk score based on linguistic and behavioral flags.
    (Corresponds to Task 4.4)
    For MVP, a simple weighted average of the maximum scores from each category is used.
    Behavioral patterns are weighted higher as they often indicate stronger intent.
    """
    linguistic_scores = [f.score for f in linguistic_flags] if linguistic_flags else [0.0]
    behavioral_scores = [f.score for f in behavioral_flags] if behavioral_flags else [0.0]

    max_linguistic_score = max(linguistic_scores)
    max_behavioral_score = max(behavioral_scores)

    # Simple weighted average. Weights can be tuned.
    # If a flag category is absent, its score is 0.
    combined_score = (max_linguistic_score * 0.4) + (max_behavioral_score * 0.6)
    return min(1.0, combined_score) # Ensure score doesn't exceed 1.0

# --- Example Usage for testing the modules ---
if __name__ == '__main__':
    print("--- Testing Linguistic Pattern Detection ---")
    review_text_1 = "This product is absolutely amazing!!! I love it so much. Truly amazing, amazing, amazing!"
    ling_flags_1 = detect_linguistic_patterns(review_text_1)
    for flag in ling_flags_1:
        print(f"  Linguistic Flag: {flag.pattern}, Score: {flag.score}, Details: {flag.details}")

    review_text_2 = "Great product! Works well."
    ling_flags_2 = detect_linguistic_patterns(review_text_2)
    for flag in ling_flags_2:
        print(f"  Linguistic Flag: {flag.pattern}, Score: {flag.score}, Details: {flag.details}")

    print("
--- Testing Behavioral Pattern Detection ---")
    # Scenario 1: New account, high frequency, extreme rating bias, single category focus
    user_history_1 = UserReviewHistory(
        user_id="user456",
        account_creation_date=datetime.now() - timedelta(days=5), # Account is 5 days old
        reviews=[
            {"review_id": "r1", "post_date": datetime.now() - timedelta(days=4, hours=1), "rating": 5, "product_category": "Electronics"},
            {"review_id": "r2", "post_date": datetime.now() - timedelta(days=4), "rating": 5, "product_category": "Electronics"},
            {"review_id": "r3", "post_date": datetime.now() - timedelta(days=3), "rating": 5, "product_category": "Electronics"},
            {"review_id": "r4", "post_date": datetime.now() - timedelta(days=2), "rating": 5, "product_category": "Electronics"},
            {"review_id": "r5", "post_date": datetime.now() - timedelta(days=1), "rating": 5, "product_category": "Electronics"},
            {"review_id": "r6", "post_date": datetime.now() - timedelta(hours=12), "rating": 5, "product_category": "Electronics"},
            {"review_id": "r7", "post_date": datetime.now() - timedelta(hours=6), "rating": 5, "product_category": "Electronics"},
        ] # 7 reviews in 5 days, all 5-star, all in 'Electronics'
    )
    beh_flags_1 = detect_behavioral_patterns(user_history_1, datetime.now())
    for flag in beh_flags_1:
        print(f"  Behavioral Flag: {flag.pattern}, Score: {flag.score}, Details: {flag.details}")

    # Scenario 2: Normal user (should not trigger flags)
    user_history_2 = UserReviewHistory(
        user_id="user123",
        account_creation_date=datetime.now() - timedelta(days=300), # Old account
        reviews=[
            {"review_id": "ra", "post_date": datetime.now() - timedelta(days=50), "rating": 4, "product_category": "Books"},
            {"review_id": "rb", "post_date": datetime.now() - timedelta(days=40), "rating": 5, "product_category": "Home Goods"},
            {"review_id": "rc", "post_date": datetime.now() - timedelta(days=30), "rating": 3, "product_category": "Electronics"},
        ] # Diverse ratings and categories over time
    )
    beh_flags_2 = detect_behavioral_patterns(user_history_2, datetime.now())
    if not beh_flags_2:
        print("  No suspicious behavioral flags detected for user2.")
    else:
        for flag in beh_flags_2:
            print(f"  Behavioral Flag: {flag.pattern}, Score: {flag.score}, Details: {flag.details}")

    print("
--- Testing Combined Risk Score ---")
    # Scenario 1: High linguistic flags, high behavioral flags
    combined_score_1 = calculate_combined_risk_score(ling_flags_1, beh_flags_1)
    print(f"  Combined Risk Score (High Ling, High Behav): {combined_score_1}") # Expected result around 0.8-0.9

    # Scenario 2: No linguistic flags, medium behavioral flags
    beh_flags_medium = [BehavioralFlag(pattern="single_category_focus", score=0.6, details={})]
    combined_score_2 = calculate_combined_risk_score([], beh_flags_medium)
    print(f"  Combined Risk Score (No Ling, Medium Behav): {combined_score_2}") # Expected 0.6 (behavioral score) * 0.6 (weight) = 0.36

    # Scenario 3: Medium linguistic flags, no behavioral flags
    ling_flags_medium = [LinguisticFlag(pattern="generic_short_praise", score=0.5, details={})]
    combined_score_3 = calculate_combined_risk_score(ling_flags_medium, [])
    print(f"  Combined Risk Score (Medium Ling, No Behav): {combined_score_3}") # Expected 0.5 (linguistic score) * 0.4 (weight) = 0.2