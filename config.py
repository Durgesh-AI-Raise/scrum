# config.py
# Review Velocity Thresholds
VELOCITY_THRESHOLD_PRODUCT = 50  # Max reviews for a product in VELOCITY_TIME_WINDOW_MINUTES
VELOCITY_TIME_WINDOW_MINUTES = 60 # Time window in minutes

# Keyword Detection Configuration
ABUSIVE_KEYWORDS = [
    "paid review", "scam", "fraud", "fake", "spam", "profanity_placeholder_1", "profanity_placeholder_2"
]
