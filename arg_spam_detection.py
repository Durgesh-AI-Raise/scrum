import re

SPAM_KEYWORDS = [
    "free money",
    "buy now",
    "limited time offer",
    "click here",
    "discount code",
    "visit our website",
    "promo code",
    "get rich quick",
    "earn cash",
    "guaranteed income",
    "lose weight fast"
]

SPAM_REGEX_PATTERNS = [
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", # Basic URL detection
    r"\b(?:whatsapp|telegram|instagram|facebook)\s*\d{10,}\b", # Social media contacts
    r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b" # Email address detection
]

def detect_spam(review_text: str) -> (bool, str):
    """
    Detects spam in a given review text based on keywords and regex patterns.
    Returns a tuple of (is_spam, detection_reason).
    """
    normalized_text = review_text.lower()

    # Keyword detection
    for keyword in SPAM_KEYWORDS:
        if keyword in normalized_text:
            return True, f"Keyword '{keyword}' detected."

    # Regex pattern detection
    for pattern in SPAM_REGEX_PATTERNS:
        if re.search(pattern, normalized_text):
            return True, f"Pattern '{pattern}' detected."

    return False, "No spam detected."
