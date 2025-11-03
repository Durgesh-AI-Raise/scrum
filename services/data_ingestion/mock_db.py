from datetime import datetime

class MockDB:
    def __init__(self):
        self.reviews = []  # Stores Review objects
        self.flagged_reviews = [] # Stores FlaggedReview objects
        self.suspicious_accounts = [] # Stores SuspiciousAccount objects

    def add_review(self, review_data):
        self.reviews.append(review_data)
        # print(f"MockDB: Added review {review_data['review_id']}")

    def get_review(self, review_id):
        for review in self.reviews:
            if review['review_id'] == review_id:
                return review
        return None

    def add_flagged_review(self, flagged_data):
        self.flagged_reviews.append(flagged_data)
        # print(f"MockDB: Flagged review {flagged_data['review_id']} for reasons: {flagged_data['flag_reason']}")

    def add_suspicious_account(self, account_data):
        # Check if account is already flagged to avoid duplicates or update reasons
        for i, acc in enumerate(self.suspicious_accounts):
            if acc['account_id'] == account_data['account_id']:
                # For simplicity, update existing reasons (could have more complex merge logic)
                acc['flag_reason'] = list(set(acc['flag_reason'] + account_data['flag_reason']))
                acc['flag_timestamp'] = datetime.now()
                acc['associated_reviews'] = list(set(acc['associated_reviews'] + account_data['associated_reviews']))
                return
        self.suspicious_accounts.append(account_data)
        # print(f"MockDB: Flagged account {account_data['account_id']} for reasons: {account_data['flag_reason']}")

    def get_reviewer_reviews(self, reviewer_id):
        return [review for review in self.reviews if review['reviewer_id'] == reviewer_id]

# Singleton instance of MockDB
mock_db = MockDB()