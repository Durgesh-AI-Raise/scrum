from datetime import datetime, timedelta
from collections import defaultdict
from services.data_ingestion.mock_db import mock_db

class AccountFlaggingService:
    def __init__(self):
        # Configurable thresholds for MVP
        self.high_velocity_threshold_count = 3 # N reviews
        self.high_velocity_threshold_days = 1 # X days
        self.new_account_age_days = 30
        self.new_account_min_reviews = 3
        self.new_account_min_5_star_percentage = 0.8 # 80%

    def detect_suspicious_accounts(self):
        reviewer_data = defaultdict(lambda: {
            'reviews': [],
            'first_review_date': datetime.max,
            'total_reviews': 0,
            'five_star_reviews': 0
        })

        for review in mock_db.reviews:
            reviewer_id = review['reviewer_id']
            reviewer_data[reviewer_id]['reviews'].append(review)
            reviewer_data[reviewer_id]['total_reviews'] += 1
            if review['rating'] == 5:
                reviewer_data[reviewer_id]['five_star_reviews'] += 1
            if review['review_date'] < reviewer_data[reviewer_id]['first_review_date']:
                reviewer_data[reviewer_id]['first_review_date'] = review['review_date']

        for reviewer_id, data in reviewer_data.items():
            flags = []
            associated_reviews = []

            # Rule 1: High Velocity of Reviews
            # Group reviews by day and check velocity
            reviews_by_day = defaultdict(int)
            for review in data['reviews']:
                day = review['review_date'].date()
                reviews_by_day[day] += 1

            for day, count in reviews_by_day.items():
                if count >= self.high_velocity_threshold_count:
                    flags.append(f"high_velocity_reviews_on_day:{day}")
                    associated_reviews.extend([r['review_id'] for r in data['reviews'] if r['review_date'].date() == day])

            # Rule 2: Newly Created Accounts with Many 5-star Reviews
            current_time = datetime.now() # Mock current time for calculation
            account_age = current_time - data['first_review_date']

            if account_age.days <= self.new_account_age_days and \
               data['total_reviews'] >= self.new_account_min_reviews and \
               (data['five_star_reviews'] / data['total_reviews']) >= self.new_account_min_5_star_percentage:
                flags.append("new_account_high_5_star_percentage")
                associated_reviews.extend([r['review_id'] for r in data['reviews']])

            if flags:
                flagged_account_data = {
                    "account_id": reviewer_id,
                    "flag_reason": list(set(flags)), # Ensure unique reasons
                    "flag_timestamp": datetime.now(),
                    "associated_reviews": list(set(associated_reviews)) # Ensure unique review IDs
                }
                mock_db.add_suspicious_account(flagged_account_data)

account_flagging_service = AccountFlaggingService()