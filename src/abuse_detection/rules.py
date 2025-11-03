
import datetime
from collections import defaultdict, Counter

# Configuration for rules (can be moved to a config file later)
NEW_ACCOUNT_DAYS_THRESHOLD = 15
REVIEW_FREQUENCY_DAYS_THRESHOLD = 7
MIN_REVIEWS_FOR_NEW_ACCOUNT_RULE = 3

NEW_PRODUCT_DAYS_THRESHOLD = 14
HIGH_VOLUME_REVIEW_THRESHOLD = 10 # Example: 10 reviews in the product's new period
PRODUCT_REVIEW_CHECK_PERIOD_DAYS = 7 # Check for high volume within this period from product launch

def _parse_date(date_str):
    """Helper to parse ISO format date strings."""
    return datetime.datetime.fromisoformat(date_str)

def rule_new_account_multiple_reviews(reviews: list) -> list:
    """
    Flags reviews where a new account submits multiple reviews in a short period.
    """
    flagged_reviews = []
    user_reviews_map = defaultdict(list)
    for review in reviews:
        user_reviews_map[review['user_id']].append(review)

    current_time = datetime.datetime.now()

    for user_id, user_reviews_list in user_reviews_map.items():
        if not user_reviews_list:
            continue

        # Assuming account_creation_date is consistent for a user across their reviews
        account_creation_date_str = user_reviews_list[0].get('account_creation_date')
        if not account_creation_date_str:
            continue # Skip if account creation date is missing

        account_creation_date = _parse_date(account_creation_date_str)
        is_new_account = (current_time - account_creation_date).days <= NEW_ACCOUNT_DAYS_THRESHOLD

        if is_new_account:
            recent_reviews_count = 0
            for review in user_reviews_list:
                review_date = _parse_date(review['review_date'])
                if (current_time - review_date).days <= REVIEW_FREQUENCY_DAYS_THRESHOLD:
                    recent_reviews_count += 1

            if recent_reviews_count >= MIN_REVIEWS_FOR_NEW_ACCOUNT_RULE:
                # Flag all recent reviews by this user that contributed to the count
                for review in user_reviews_list:
                    review_date = _parse_date(review['review_date'])
                    if (current_time - review_date).days <= REVIEW_FREQUENCY_DAYS_THRESHOLD:
                         # Add a deep copy or just the ID to avoid modifying original list during iteration
                         flagged_reviews.append(review)
    return flagged_reviews

def rule_high_volume_new_product_reviews(reviews: list) -> list:
    """
    Flags reviews for a new product that receives an unusually high volume of reviews.
    """
    flagged_reviews = []
    product_reviews_map = defaultdict(list)
    for review in reviews:
        product_reviews_map[review['product_id']].append(review)

    current_time = datetime.datetime.now()

    for product_id, product_reviews_list in product_reviews_map.items():
        if not product_reviews_list:
            continue

        product_launch_date_str = product_reviews_list[0].get('product_launch_date')
        if not product_launch_date_str:
            continue # Skip if product launch date is missing

        product_launch_date = _parse_date(product_launch_date_str)
        is_new_product = (current_time - product_launch_date).days <= NEW_PRODUCT_DAYS_THRESHOLD

        if is_new_product:
            recent_product_reviews_count = 0
            reviews_in_check_period = []
            for review in product_reviews_list:
                review_date = _parse_date(review['review_date'])
                if (current_time - review_date).days <= PRODUCT_REVIEW_CHECK_PERIOD_DAYS:
                    recent_product_reviews_count += 1
                    reviews_in_check_period.append(review)

            if recent_product_reviews_count >= HIGH_VOLUME_REVIEW_THRESHOLD:
                # Flag all reviews for this new product in the check period
                flagged_reviews.extend(reviews_in_check_period)
    return flagged_reviews

def rule_identical_content_across_products(reviews: list) -> list:
    """
    Flags reviews where identical content is posted across different products.
    """
    flagged_reviews = []
    content_to_review_info_map = defaultdict(list) # {review_text: [{review_id, product_id, user_id, original_review_object}, ...]}

    for review in reviews:
        content = review.get('review_text')
        if content:
            content_to_review_info_map[content].append({
                'review_id': review['review_id'],
                'product_id': review['product_id'],
                'user_id': review['user_id'],
                'original_review_object': review # Reference to the original object
            })

    for content, review_infos in content_to_review_info_map.items():
        if len(review_infos) > 1:
            # Check if this content appears across multiple distinct products
            product_ids = {info['product_id'] for info in review_infos}
            if len(product_ids) > 1:
                # If identical content is found across different products, flag all occurrences
                for info in review_infos:
                    flagged_reviews.append(info['original_review_object'])
    return flagged_reviews
