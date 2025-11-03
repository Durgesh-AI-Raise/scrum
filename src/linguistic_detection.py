import re
from collections import Counter

class LinguisticDetector:
    def __init__(self, keyword_stuffing_threshold=3, sentiment_threshold=0.7):
        self.keyword_stuffing_threshold = keyword_stuffing_threshold
        self.sentiment_threshold = sentiment_threshold
        # Simple lexicon for sentiment analysis
        self.positive_words = {"amazing", "love", "fantastic", "superb", "excellent", "great", "wonderful", "best"}
        self.negative_words = {"terrible", "worst", "disappointed", "bad", "horrible", "awful", "poor"}

    def detect_keyword_stuffing(self, text: str) -> tuple[bool, float]:
        words = re.findall(r'\b\w+\b', text.lower())
        word_counts = Counter(words)
        for word, count in word_counts.items():
            # Ignore very short common words for keyword stuffing detection
            if count >= self.keyword_stuffing_threshold and len(word) > 2 and word not in {"the", "a", "is", "it", "of", "and"}:
                # Simple confidence score based on how much the count exceeds the threshold
                confidence = min(1.0, (count - self.keyword_stuffing_threshold + 1) / 5.0)
                return True, confidence
        return False, 0.0

    def detect_extreme_sentiment(self, text: str) -> tuple[bool, float]:
        words = re.findall(r'\b\w+\b', text.lower())
        pos_score = sum(1 for word in words if word in self.positive_words)
        neg_score = sum(1 for word in words if word in self.negative_words)
        total_sentiment_words = pos_score + neg_score

        if total_sentiment_words == 0:
            return False, 0.0

        sentiment_ratio = (pos_score - neg_score) / total_sentiment_words

        if sentiment_ratio >= self.sentiment_threshold:
            return True, sentiment_ratio
        elif sentiment_ratio <= -self.sentiment_threshold:
            return True, abs(sentiment_ratio) # Report absolute confidence for negative extreme sentiment
        return False, 0.0