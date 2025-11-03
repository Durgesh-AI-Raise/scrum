from datetime import datetime, timedelta

# Mock data repositories for demonstration
class MockAccountRepository:
    def get_account(self, account_id: str):
        # In a real system, this would query a database
        accounts = {
            "acc_1": {"creation_date": datetime.now() - timedelta(days=5)}, # New, suspicious
            "acc_2": {"creation_date": datetime.now() - timedelta(days=365)}, # Old, normal
            "acc_3": {"creation_date": datetime.now() - timedelta(days=10)}, # Medium age
            "acc_4": {"creation_date": datetime.now() - timedelta(days=2)}, # Very new
        }
        return accounts.get(account_id)

class MockReviewRepository:
    def get_reviews_by_account(self, account_id: str):
        # In a real system, this would query a database
        reviews = {
            "acc_1": [ # New account, many 5-star for diverse products
                {"rating": 5, "timestamp": datetime.now() - timedelta(hours=1), "product_id": "prod_A", "product_category": "Electronics"},
                {"rating": 5, "timestamp": datetime.now() - timedelta(hours=2), "product_id": "prod_B", "product_category": "Books"},
                {"rating": 5, "timestamp": datetime.now() - timedelta(hours=3), "product_id": "prod_C", "product_category": "Clothing"},
                {"rating": 5, "timestamp": datetime.now() - timedelta(hours=4), "product_id": "prod_D", "product_category": "Food"},
            ],
            "acc_2": [ # Old account, normal reviews
                {"rating": 4, "timestamp": datetime.now() - timedelta(days=30), "product_id": "prod_E", "product_category": "Electronics"},
                {"rating": 5, "timestamp": datetime.now() - timedelta(days=60), "product_id": "prod_F", "product_category": "Home"},
            ],
            "acc_3": [ # Medium age, all 1-star for competitors
                {"rating": 1, "timestamp": datetime.now() - timedelta(hours=5), "product_id": "comp_X", "product_category": "Electronics"},
                {"rating": 1, "timestamp": datetime.now() - timedelta(hours=6), "product_id": "comp_Y", "product_category": "Electronics"},
            ],
             "acc_4": [ # Very new, high volume of 5-star reviews for same product in short span
                {"rating": 5, "timestamp": datetime.now() - timedelta(hours=1), "product_id": "prod_Z", "product_category": "Books"},
                {"rating": 5, "timestamp": datetime.now() - timedelta(hours=1, minutes=5), "product_id": "prod_Z", "product_category": "Books"},
                {"rating": 5, "timestamp": datetime.now() - timedelta(hours=1, minutes=10), "product_id": "prod_Z", "product_category": "Books"},
                {"rating": 5, "timestamp": datetime.now() - timedelta(hours=1, minutes=15), "product_id": "prod_Z", "product_category": "Books"},
                {"rating": 5, "timestamp": datetime.now() - timedelta(hours=1, minutes=20), "product_id": "prod_Z", "product_category": "Books"},
            ],
        }
        return reviews.get(account_id, [])

class SuspiciousAccountDetectionService:
    def __init__(self, account_repo: MockAccountRepository, review_repo: MockReviewRepository):
        self.account_repo = account_repo
        self.review_repo = review_repo
        self.SUSPICIOUS_ACCOUNT_AGE_DAYS = 7
        self.HIGH_REVIEW_VOLUME_THRESHOLD = 5 # reviews in a short period (e.g., 24 hours)
        self.REVIEW_VOLUME_CHECK_PERIOD_HOURS = 24
        self.MIN_DIVERSE_CATEGORIES = 3 # for high 5-star reviews
        self.MIN_ONE_STAR_REVIEWS_FOR_COMPETITORS = 2

    def detect_suspicion(self, account_id: str) -> dict:
        account = self.account_repo.get_account(account_id)
        if not account:
            return {"is_suspicious": False, "reasons": ["Account not found"]}

        reviews = self.review_repo.get_reviews_by_account(account_id)
        reasons = []

        # Heuristic 1: New account with high activity
        account_age_days = (datetime.now() - account["creation_date"]).days
        if account_age_days < self.SUSPICIOUS_ACCOUNT_AGE_DAYS:
            reasons.append(f"Account is new (created {account_age_days} days ago).")
            # Check for high review volume in short period for new accounts
            recent_reviews = [
                r for r in reviews
                if datetime.now() - r["timestamp"] < timedelta(hours=self.REVIEW_VOLUME_CHECK_PERIOD_HOURS)
            ]
            if len(recent_reviews) >= self.HIGH_REVIEW_VOLUME_THRESHOLD:
                reasons.append(f"High review volume ({len(recent_reviews)} reviews) in the last {self.REVIEW_VOLUME_CHECK_PERIOD_HOURS} hours for a new account.")

        # Heuristic 2: All 5-star reviews across diverse, unrelated products
        if reviews:
            five_star_reviews = [r for r in reviews if r["rating"] == 5]
            if len(five_star_reviews) == len(reviews) and len(reviews) > 0: # All reviews are 5-star
                product_categories = {r["product_category"] for r in five_star_reviews}
                if len(product_categories) >= self.MIN_DIVERSE_CATEGORIES:
                    reasons.append(f"Account has only 5-star reviews across {len(product_categories)} diverse product categories.")

        # Heuristic 3: Only 1-star reviews for competitor products
        if reviews:
            one_star_reviews = [r for r in reviews if r["rating"] == 1]
            if len(one_star_reviews) >= self.MIN_ONE_STAR_REVIEWS_FOR_COMPETITORS and len(one_star_reviews) == len(reviews):
                # A more sophisticated check would involve identifying 'competitor products'
                # For now, let's assume if all reviews are 1-star and there are enough of them, it's suspicious
                reasons.append(f"Account has only 1-star reviews ({len(one_star_reviews)} reviews) suggesting targeted negative campaigning.")

        return {
            "is_suspicious": len(reasons) > 0,
            "reasons": reasons,
            "confidence_score": "High" if len(reasons) >= 2 else ("Medium" if len(reasons) == 1 else "Low")
        }

# Example Usage (for testing the service logic)
if __name__ == "__main__":
    account_repo = MockAccountRepository()
    review_repo = MockReviewRepository()
    service = SuspiciousAccountDetectionService(account_repo, review_repo)

    print("--- Account 1 ---")
    result1 = service.detect_suspicion("acc_1")
    print(result1) # Expected: suspicious due to new account + diverse 5-star

    print("
--- Account 2 ---")
    result2 = service.detect_suspicion("acc_2")
    print(result2) # Expected: not suspicious

    print("
--- Account 3 ---")
    result3 = service.detect_suspicion("acc_3")
    print(result3) # Expected: suspicious due to only 1-star reviews

    print("
--- Account 4 ---")
    result4 = service.detect_suspicion("acc_4")
    print(result4) # Expected: suspicious due to very new + high volume reviews

    print("
--- Non-existent Account ---")
    result_non_existent = service.detect_suspicion("acc_X")
    print(result_non_existent) # Expected: not suspicious, account not found
