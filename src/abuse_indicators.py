# src/abuse_indicators.py

ABUSE_KEYWORDS = {
    "excessive_praise": [
        "amazing product", "best ever", "love this", "highly recommend", "flawless", "perfect", "game changer",
        "must buy", "life-changing", "incredible", "superb", "outstanding", "fantastic", "excellent",
        "top-notch", "five stars", "beyond expectations", "absolutely love", "greatest", "wonderful",
        "perfectly", "superb", "fantastic", "ideal", "brilliant", "magnificent", "awesome", "tremendous"
    ],
    "negative_keywords": [
        "scam", "fraud", "horrible", "waste of money", "terrible", "fake", "deceptive",
        "awful", "disappointed", "poor quality", "broken", "unusable", "ripoff", "defective",
        "never again", "beware", "useless", "bad", "worst", "hate", "regret", "fail", "broken",
        "malfunction", "faulty", "return", "refund", "unacceptable"
    ],
    "irrelevant_content": [
        "shipping was fast", "package arrived on time", "seller was good", "delivery was great",
        "received quickly", "fast delivery", "well packaged", "good seller", "product arrived",
        "thank you for your order", "happy with seller", "arrived safe", "box was damaged",
        "postage was quick", "courier service", "dispatch time"
    ],
    "ai_generated_patterns": [
        "as an AI language model", "I cannot express personal opinions", "in conclusion", "furthermore",
        "overall satisfaction", "in summary", "my analysis indicates", "I am an AI",
        "based on my understanding", "this product offers", "various features include",
        "it is worth noting", "to reiterate", "ultimately", "it can be said that", "highlights include",
        "key takeaways", "in essence"
    ],
    "spam_phrases": [
        "click here", "buy now", "free gift", "discount code", "limited time offer",
        "visit our website", "promotion", "coupon", "deal", "earn money", "exclusive offer",
        "check out my store", "get yours today", "link in bio", "affiliate", "promo code",
        "giveaway", "win a prize"
    ]
}
