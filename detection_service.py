from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import statistics

@dataclass
class Review:
    review_id: str
    product_asin: str
    reviewer_id: str
    rating: int
    review_text: str
    review_date: datetime
    is_flagged: bool = False
    flag_details: List[Dict[str, Any]] = field(default_factory=list)
    predicted_abuse_type: Optional[str] = None
    severity_score: int = 0
    is_confirmed_abusive: Optional[bool] = None
    confirmed_abuse_category: Optional[str] = None
    confirmation_date: Optional[datetime] = None

@dataclass
class Reviewer:
    reviewer_id: str
    username: str
    email: str
    registration_date: datetime
    total_reviews: int
    average_rating: float
    geographic_data: Optional[str] = None
    linked_accounts: List[str] = field(default_factory=list)
    reviewer_history: List[Dict[str, Any]] = field(default_factory=list) # e.g., [{"review_id": "R1", "rating": 5}]
    is_flagged_as_reviewer: bool = False
    reviewer_flag_details: List[Dict[str, Any]] = field(default_factory=list)

# --- Configuration Constants ---
MIN_REVIEWS_FOR_STATS = 5
THRESHOLD_STD_DEV = 2.0 # For unusual rating
RAPID_POSTING_WINDOW_MINUTES = 60
RAPID_POSTING_THRESHOLD_COUNT = 5
KEYWORD_DENSITY_THRESHOLD = 0.05 # 5% of words are "stuffing" keywords
ABUSIVE_KEYWORDS = ["buy now", "best ever", "great deal", "must have", "free money", "scam alert"]

# --- Helper Functions ---
def calculate_stats(data: List[float]) -> tuple[float, float]:
    if not data:
        return 0.0, 0.0
    avg = statistics.mean(data)
    std_dev = statistics.stdev(data) if len(data) > 1 else 0.0
    return avg, std_dev

# --- Detection Logic ---
def detect_unusual_rating(review: Review, reviewer_history: List[Review], product_reviews: List[Review]) -> dict:
    reviewer_ratings = [r.rating for r in reviewer_history if r.review_id != review.review_id]
    product_ratings = [r.rating for r in product_reviews if r.review_id != review.review_id]

    is_suspicious = False
    details = {}
    
    # Check against reviewer's history
    if len(reviewer_ratings) >= MIN_REVIEWS_FOR_STATS:
        avg_reviewer_rating, std_reviewer_rating = calculate_stats(reviewer_ratings)
        if std_reviewer_rating > 0 and abs(review.rating - avg_reviewer_rating) > THRESHOLD_STD_DEV * std_reviewer_rating:
            is_suspicious = True
            details["reason"] = "Unusual rating compared to reviewer's history"
            details["deviation"] = review.rating - avg_reviewer_rating

    # Check against product's average if not already suspicious or not enough reviewer history
    if not is_suspicious and len(product_ratings) >= MIN_REVIEWS_FOR_STATS:
        avg_product_rating, std_product_rating = calculate_stats(product_ratings)
        if std_product_rating > 0 and abs(review.rating - avg_product_rating) > THRESHOLD_STD_DEV * std_product_rating:
            is_suspicious = True
            details["reason"] = "Unusual rating compared to product's average"
            details["deviation"] = review.rating - avg_product_rating

    return {"is_suspicious": is_suspicious, "details": details}

def detect_rapid_posting(reviewer_id: str, current_review_date: datetime, recent_reviews: List[Review]) -> dict:
    suspicious_count = 0
    for review in recent_reviews:
        # Check reviews older than current but within window
        if review.review_date < current_review_date:
            time_diff = (current_review_date - review.review_date).total_seconds() / 60 # in minutes
            if time_diff <= RAPID_POSTING_WINDOW_MINUTES:
                suspicious_count += 1
    
    # Add the current review to the count for threshold check
    if suspicious_count + 1 >= RAPID_POSTING_THRESHOLD_COUNT: # +1 for the current review being evaluated
        is_suspicious = True
    else:
        is_suspicious = False

    details = {"count": suspicious_count + 1, "window_minutes": RAPID_POSTING_WINDOW_MINUTES}
    return {"is_suspicious": is_suspicious, "details": details}

def detect_keyword_stuffing(review_text: str) -> dict:
    text_lower = review_text.lower()
    words = text_lower.split()
    word_count = len(words)

    if word_count == 0:
        return {"is_suspicious": False, "details": {"density": 0.0, "detected_keywords": []}}

    stuffed_keywords_count = 0
    detected_keywords = []

    for keyword in ABUSIVE_KEYWORDS:
        if keyword in text_lower:
            # Count occurrences of exact keyword or phrase
            count = text_lower.count(keyword)
            stuffed_keywords_count += count
            if count > 0 and keyword not in detected_keywords: # Avoid duplicates in detected_keywords list
                detected_keywords.append(keyword)

    density = stuffed_keywords_count / word_count
    is_suspicious = density > KEYWORD_DENSITY_THRESHOLD
    
    details = {"density": round(density, 4), "detected_keywords": detected_keywords}
    return {"is_suspicious": is_suspicious, "details": details}

# --- Flagging Orchestration ---
def determine_abuse_type(flags: List[Dict[str, Any]]) -> str:
    """Maps detected flags to a primary abuse type."""
    if any(f["type"] == "rapid_posting" for f in flags):
        return "Spam"
    if any(f["type"] == "keyword_stuffing" for f in flags):
        return "Keyword Stuffing"
    if any(f["type"] == "unusual_rating" for f in flags):
        return "Rating Manipulation"
    return "General Abuse" # Fallback

def calculate_severity_score(flags: List[Dict[str, Any]]) -> int:
    """Calculates an additive severity score based on triggered flags."""
    score = 0
    for flag in flags:
        if flag["type"] == "rapid_posting":
            score += 40
        elif flag["type"] == "unusual_rating":
            score += 30
        elif flag["type"] == "keyword_stuffing":
            score += 25
        # Add more scoring logic for other types of flags
    return min(100, score) # Cap score at 100

def flag_review_service(review_data: Dict[str, Any]) -> Review:
    """
    Main service function to detect abuse and flag a review.
    In a real system, this would interact with a database.
    """
    review = Review(**review_data)
    flag_results = []

    # Mock DB interaction for detection functions
    reviewer_history_mock = get_reviewer_history(review.reviewer_id)
    product_reviews_mock = get_product_reviews(review.product_asin)
    recent_reviews_mock = get_recent_reviews(review.reviewer_id)

    # Call detection functions
    rating_flag = detect_unusual_rating(review, reviewer_history_mock, product_reviews_mock)
    if rating_flag["is_suspicious"]:
        flag_results.append({"type": "unusual_rating", "details": rating_flag["details"]})

    rapid_posting_flag = detect_rapid_posting(review.reviewer_id, review.review_date, recent_reviews_mock)
    if rapid_posting_flag["is_suspicious"]:
        flag_results.append({"type": "rapid_posting", "details": rapid_posting_flag["details"]})

    keyword_stuffing_flag = detect_keyword_stuffing(review.review_text)
    if keyword_stuffing_flag["is_suspicious"]:
        flag_results.append({"type": "keyword_stuffing", "details": keyword_stuffing_flag["details"]})

    if flag_results:
        review.is_flagged = True
        review.flag_details = flag_results
        review.severity_score = calculate_severity_score(flag_results)
        review.predicted_abuse_type = determine_abuse_type(flag_results)
    else:
        review.is_flagged = False
        review.severity_score = 0
        review.predicted_abuse_type = None

    # Simulate saving/updating the review in DB
    save_review_to_db(review)
    return review

# --- Mock Database Interaction Functions (for demonstration) ---
MOCK_REVIEWS_DB = {}
MOCK_REVIEWERS_DB = {}

# Populate mock data
def _populate_mock_data():
    global MOCK_REVIEWS_DB, MOCK_REVIEWERS_DB
    
    # Mock Reviewer Data
    reviewer1 = Reviewer(
        reviewer_id="U1", username="GoodReviewer", email="u1@example.com",
        registration_date=datetime(2022, 1, 1), total_reviews=100, average_rating=4.5,
        geographic_data="USA, New York"
    )
    reviewer2 = Reviewer(
        reviewer_id="U2", username="Spammer", email="u2@example.com",
        registration_date=datetime(2023, 5, 10), total_reviews=7, average_rating=2.0,
        geographic_data="Global"
    )
    reviewer3 = Reviewer(
        reviewer_id="U3", username="HonestCritique", email="u3@example.com",
        registration_date=datetime(2021, 11, 15), total_reviews=30, average_rating=3.8,
        geographic_data="Canada"
    )
    MOCK_REVIEWERS_DB = {r.reviewer_id: r for r in [reviewer1, reviewer2, reviewer3]}

    # Mock Review Data
    reviews_list = [
        Review(
            review_id="R101", product_asin="P1001", reviewer_id="U1", rating=5,
            review_text="This is an excellent product, highly recommend!",
            review_date=datetime.now() - timedelta(days=50)
        ),
        Review(
            review_id="R102", product_asin="P1002", reviewer_id="U1", rating=4,
            review_text="Good value for money, slightly slow shipping.",
            review_date=datetime.now() - timedelta(days=45)
        ),
        Review(
            review_id="R201", product_asin="P1003", reviewer_id="U2", rating=1,
            review_text="Absolute rubbish! Do not buy now! Horrible experience, best ever avoided.",
            review_date=datetime.now() - timedelta(minutes=70) # Just outside rapid posting window for R202
        ),
        Review(
            review_id="R202", product_asin="P1003", reviewer_id="U2", rating=1,
            review_text="Terrible product. Buy now for a regretful experience. Great deal if you hate quality.",
            review_date=datetime.now() - timedelta(minutes=50)
        ),
        Review(
            review_id="R203", product_asin="P1004", reviewer_id="U2", rating=1,
            review_text="Another bad product. Avoid at all costs, buy now or miss out on pain. Free money gone.",
            review_date=datetime.now() - timedelta(minutes=40)
        ),
        Review(
            review_id="R204", product_asin="P1005", reviewer_id="U2", rating=1,
            review_text="Worst purchase. Absolute scam alert! Free money lost.",
            review_date=datetime.now() - timedelta(minutes=30)
        ),
        Review(
            review_id="R205", product_asin="P1006", reviewer_id="U2", rating=5, # Unusual rating for U2
            review_text="This product is surprisingly good. Best ever!",
            review_date=datetime.now() - timedelta(minutes=20)
        ),
        Review(
            review_id="R301", product_asin="P1001", reviewer_id="U3", rating=3,
            review_text="It's okay, nothing special. Met expectations.",
            review_date=datetime.now() - timedelta(days=10)
        )
    ]
    MOCK_REVIEWS_DB = {r.review_id: r for r in reviews_list}

    # Simulate initial flagging for some reviews to have flagged data
    for review_id in ["R202", "R203", "R204", "R205"]:
        review_to_flag = MOCK_REVIEWS_DB[review_id]
        flagged_result = flag_review_service(review_to_flag.__dict__)
        MOCK_REVIEWS_DB[review_id] = flagged_result

_populate_mock_data() # Initialize mock data on module load

def get_reviewer_history(reviewer_id: str) -> List[Review]:
    """Retrieves all reviews by a specific reviewer."""
    return [r for r in MOCK_REVIEWS_DB.values() if r.reviewer_id == reviewer_id]

def get_product_reviews(product_asin: str) -> List[Review]:
    """Retrieves all reviews for a specific product."""
    return [r for r in MOCK_REVIEWS_DB.values() if r.product_asin == product_asin]

def get_recent_reviews(reviewer_id: str) -> List[Review]:
    """Retrieves recent reviews for a reviewer within a specific timeframe (e.g., last 2 hours)."""
    two_hours_ago = datetime.now() - timedelta(hours=2)
    return [r for r in MOCK_REVIEWS_DB.values() if r.reviewer_id == reviewer_id and r.review_date > two_hours_ago]

def save_review_to_db(review: Review):
    """Mocks saving/updating a review in the database."""
    MOCK_REVIEWS_DB[review.review_id] = review
    # print(f"Mock DB: Saved/Updated review {review.review_id}. Flagged: {review.is_flagged}, Severity: {review.severity_score}")

def get_review_by_id_from_db(review_id: str) -> Optional[Review]:
    """Mocks retrieving a single review by ID."""
    return MOCK_REVIEWS_DB.get(review_id)

def get_reviewer_by_id_from_db(reviewer_id: str) -> Optional[Reviewer]:
    """Mocks retrieving a single reviewer by ID."""
    return MOCK_REVIEWERS_DB.get(reviewer_id)

def update_review_in_db(review: Review):
    """Mocks updating an existing review in the database."""
    if review.review_id in MOCK_REVIEWS_DB:
        MOCK_REVIEWS_DB[review.review_id] = review
    else:
        print(f"Error: Review {review.review_id} not found for update.")

def log_for_learning(review: Review):
    """Mocks logging confirmed abuse for future model training."""
    print(f"Logged for learning: Review {review.review_id} confirmed as {review.is_confirmed_abusive} in category {review.confirmed_abuse_category}")

def get_flagged_reviews_from_db(page: int, limit: int, sort_by: str, sort_order: str) -> List[Review]:
    """Mocks retrieving flagged reviews from the database."""
    all_flagged_reviews = [r for r in MOCK_REVIEWS_DB.values() if r.is_flagged]
    
    # Sort
    if sort_by in Review.__dataclass_fields__:
        all_flagged_reviews.sort(key=lambda x: getattr(x, sort_by), reverse=(sort_order == 'desc'))
    else:
        print(f"Warning: Cannot sort by unknown field '{sort_by}'. Using default order.")

    # Paginate
    start = (page - 1) * limit
    end = start + limit
    return all_flagged_reviews[start:end]

def get_flagged_reviews_from_db_with_filters(page: int, limit: int, sort_by: str, sort_order: str, filters: Dict[str, Any]) -> List[Review]:
    """Mocks retrieving flagged reviews with filtering."""
    all_reviews = [r for r in MOCK_REVIEWS_DB.values() if r.is_flagged]
    filtered_reviews = []

    for review in all_reviews:
        match = True
        if filters.get("product_asin") and filters["product_asin"] != review.product_asin:
            match = False
        if filters.get("reviewer_id") and filters["reviewer_id"] != review.reviewer_id:
            match = False
        if filters.get("abuse_type") and filters["abuse_type"] != review.predicted_abuse_type:
            match = False
        if filters.get("min_severity") is not None and review.severity_score < filters["min_severity"]:
            match = False
        if filters.get("max_severity") is not None and review.severity_score > filters["max_severity"]:
            match = False
        
        start_date_str = filters.get("start_date")
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            if review.review_date.date() < start_date:
                match = False
        
        end_date_str = filters.get("end_date")
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if review.review_date.date() > end_date:
                match = False
        
        search_text = filters.get("search_text")
        if search_text and search_text.lower() not in review.review_text.lower():
            match = False

        if match:
            filtered_reviews.append(review)

    # Sort after filtering
    if sort_by in Review.__dataclass_fields__:
        filtered_reviews.sort(key=lambda x: getattr(x, sort_by), reverse=(sort_order == 'desc'))
    
    # Paginate
    start = (page - 1) * limit
    end = start + limit
    return filtered_reviews[start:end]