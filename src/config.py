
POST_LAUNCH_WINDOW_DAYS = 60
MIN_POSITIVE_RATING_THRESHOLD = 4.5
MIN_REVIEW_COUNT_FOR_SPIKE = 20 # To avoid false positives on low review count

# For User Story 1.2
MIN_REVIEWS_FOR_SELLER_NETWORK = 10
MIN_DISTINCT_PRODUCTS_FOR_SELLER_NETWORK = 3
MIN_AVG_RATING_FOR_SELLER_NETWORK = 4.0

# For User Story 1.3
ABUSIVE_KEYWORDS = [
    "free product for review",
    "received discount for review",
    "profanityword1", # Placeholder for actual profanity
    "profanityword2",
    "bought this for free",
    "exchange for review",
    "incentivized review"
]
