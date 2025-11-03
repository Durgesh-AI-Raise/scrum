from review_connector import ReviewDataConnector
from pattern_detector import ReviewPatternDetector
from flagged_review_storage import FlaggedReviewStorage
from datetime import datetime

def run_detection_pipeline():
    """
    Orchestrates the data flow from connector to detector to storage.
    """
    print("Starting review burst detection pipeline...")

    # 1. Initialize Components
    connector = ReviewDataConnector()
    detector = ReviewPatternDetector(burst_time_window_hours=1, burst_threshold_reviews=10) # 10 reviews in 1 hour
    storage = FlaggedReviewStorage()

    # 2. Fetch Review Data
    print("Fetching recent reviews...")
    all_reviews = connector.fetch_recent_reviews(limit=200) # Fetch up to 200 mock reviews
    print(f"Fetched {len(all_reviews)} reviews.")

    # 3. Detect Suspicious Patterns
    print("Detecting review bursts...")
    flagged_reviews = detector.detect_bursts(all_reviews)
    print(f"Detected {len(flagged_reviews)} suspicious reviews.")

    # 4. Store Flagged Reviews
    if flagged_reviews:
        print("Storing flagged reviews...")
        for flagged_review in flagged_reviews:
            storage.save_flagged_review(flagged_review)
    else:
        print("No suspicious reviews to store.")

    print("
Pipeline finished.")
    # Optional: Display all flagged reviews after the run
    # print("
--- All Flagged Reviews ---")
    # for fr in storage.get_all_flagged_reviews():
    #     print(f"ID: {fr.review_id}, Product: {fr.product_id}, Pattern: {fr.pattern_type}, Reason: {fr.reason}")

if __name__ == "__main__":
    run_detection_pipeline()
