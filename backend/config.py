
# backend/config.py

# Configuration for spam account flagging
SPAM_ACCOUNT_FLAGGING_CONFIG = {
    "min_reviews_count": 5,          # Minimum number of reviews within the time period
    "time_period_hours": 72,         # Time window in hours (e.g., 72 hours = 3 days)
    "min_distinct_products": 3,      # Minimum distinct products reviewed
    "min_distinct_sellers": 2,       # Minimum distinct sellers reviewed
}

# Initial list of suspicious keywords for review text scanning
SUSPICIOUS_KEYWORDS = [
    "paid review",
    "discount for review",
    "free product for review",
    "incentivized review",
    "honest review in exchange for",
    "complimentary product for review",
    "received this product for free",
    "sponsored post",
    "gifted item for review",
]
