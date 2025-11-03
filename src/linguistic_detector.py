import re
import json
from textblob import TextBlob
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinguisticDetector:
    def __init__(self, rules_filepath='config/linguistic_rules.json'):
        self.rules = self._load_rules(rules_filepath)
        logger.info("LinguisticDetector initialized with rules.")

    def _load_rules(self, filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Linguistic rules file not found at {filepath}. Using empty rules.")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {filepath}. Using empty rules.")
            return {}

    def detect(self, review_text: str) -> dict:
        flagged = False
        reasons = []

        if not review_text:
            return {"is_flagged": False, "reasons": []}

        # Rule 1: Check for specific negative keywords
        negative_keywords = self.rules.get("negative_keywords", [])
        for keyword in negative_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', review_text, re.IGNORECASE):
                flagged = True
                reasons.append(f"Contains suspicious keyword: '{keyword}'")

        # Rule 2: Basic Sentiment Analysis for extremely negative reviews
        if self.rules.get("enable_sentiment_analysis", False):
            try:
                analysis = TextBlob(review_text)
                sentiment_threshold = self.rules.get("sentiment_threshold", -0.8)
                if analysis.sentiment.polarity < sentiment_threshold:
                    flagged = True
                    reasons.append(f"Extremely negative sentiment (score: {analysis.sentiment.polarity:.2f})")
            except Exception as e:
                logger.warning(f"Sentiment analysis failed for review: {e}")

        # Rule 3: Check for unusual character repetitions (e.g., "!!!!!", "????"")
        if self.rules.get("enable_repetition_check", False):
            if re.search(r'(.)\1{3,}', review_text): # 4 or more repetitions of any character
                flagged = True
                reasons.append("Unusual character repetition detected")

        # Rule 4: Check for excessive capitalization
        if self.rules.get("enable_caps_check", False):
            if len(review_text) > 20: # only for longer reviews to avoid flagging short, all-caps words
                uppercase_count = sum(1 for c in review_text if c.isupper())
                alpha_count = sum(1 for c in review_text if c.isalpha())
                if alpha_count > 0:
                    uppercase_ratio = uppercase_count / alpha_count
                    caps_threshold = self.rules.get("caps_threshold", 0.5)
                    if uppercase_ratio > caps_threshold:
                        flagged = True
                        reasons.append(f"Excessive capitalization (ratio: {uppercase_ratio:.2f})")
        
        # Rule 5: Check for spam-like phrases
        spam_phrases = self.rules.get("spam_phrases", [])
        for phrase in spam_phrases:
            if re.search(r'\b' + re.escape(phrase) + r'\b', review_text, re.IGNORECASE):
                flagged = True
                reasons.append(f"Contains spam-like phrase: '{phrase}'")

        return {"is_flagged": flagged, "reasons": list(set(reasons))} # Return unique reasons

if __name__ == "__main__":
    # Example Usage
    detector = LinguisticDetector()
    
    print("--- Test Case 1: Spam keywords and negative sentiment ---")
    result1 = detector.detect("This product is a SCAM!!!!! DO NOT BUY!!!!! Absolutely terrible!!!!")
    print(result1)

    print("\n--- Test Case 2: Excessive capitalization and repetition ---")
    result2 = detector.detect("AMAZING PRODUCT!!!!!! I LOVE IT SO MUCH. BEST EVER!!!")
    print(result2)

    print("\n--- Test Case 3: Neutral review ---")
    result3 = detector.detect("This product works as expected.")
    print(result3)

    print("\n--- Test Case 4: Review with spam phrase ---")
    result4 = detector.detect("Get a free gift with your purchase! Click here now.")
    print(result4)
