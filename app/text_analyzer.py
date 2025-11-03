import spacy
from typing import List, Dict, Any

# Load a pre-trained spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'. This will happen only once.")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

class TextAnalyzer:
    def __init__(self):
        self.nlp = nlp
        # Define keywords, phrases, or patterns for abuse detection
        self.unnatural_phrasing_patterns = [
            # Example: Rule-based patterns for unnatural phrasing
            # This can be extended with more sophisticated rules or ML models
            {"LIKE_PATTERNS": [{"POS": "ADJ", "OP": "+"}, {"POS": "ADJ", "OP": "+"}, {"POS": "NOUN", "OP": "+"}]},
        ]
        self.repeated_keywords = ["amazing", "fantastic", "terrible", "horrible"]
        self.generic_praise_keywords = ["great product", "love it", "highly recommend"]
        self.generic_criticism_keywords = ["bad quality", "waste of money", "don't buy"]

    def analyze(self, review_id: str, text: str) -> List[Dict[str, Any]]:
        doc = self.nlp(text)
        flags = []

        # 1. Unnatural Phrasing Detection
        # This is a placeholder for more advanced NLP techniques
        matcher = spacy.matcher.Matcher(self.nlp.vocab)
        for pattern in self.unnatural_phrasing_patterns:
            matcher.add("UNNATURAL_PHRASING", [pattern])

        matches = matcher(doc)
        if matches:
            # A simplified scoring - real scoring would be more complex
            suspicion_score = min(0.8, len(matches) * 0.2) # Max 0.8 for rule-based
            flags.append({
                "review_id": review_id,
                "flag_type": "unnatural_phrasing",
                "suspicion_score": suspicion_score,
                "detection_details": {"matched_phrases": [doc[start:end].text for match_id, start, end in matches]}
            })

        # 2. Repeated Keywords Detection
        token_counts = {token.text.lower(): doc.count_by_token_hash(token.orth) for token in doc if not token.is_stop and not token.is_punct}
        for keyword in self.repeated_keywords:
            if keyword in token_counts and token_counts[keyword] > 2: # More than 2 occurrences
                suspicion_score = min(0.7, token_counts[keyword] * 0.15) # Max 0.7
                flags.append({
                    "review_id": review_id,
                    "flag_type": "repeated_keywords",
                    "suspicion_score": suspicion_score,
                    "detection_details": {"keyword": keyword, "count": token_counts[keyword]}
                })
        
        # 3. Overly Generic Praise/Criticism
        for phrase in self.generic_praise_keywords:
            if phrase.lower() in text.lower():
                flags.append({
                    "review_id": review_id,
                    "flag_type": "overly_generic_praise",
                    "suspicion_score": 0.6,
                    "detection_details": {"matched_phrase": phrase}
                })
        for phrase in self.generic_criticism_keywords:
            if phrase.lower() in text.lower():
                flags.append({
                    "review_id": review_id,
                    "flag_type": "overly_generic_criticism",
                    "suspicion_score": 0.6,
                    "detection_details": {"matched_phrase": phrase}
                })

        # 4. Unrelated Content (Placeholder - requires more sophisticated topic modeling or external context)
        # For now, a very basic heuristic: check for extremely short reviews with no strong sentiment or product keywords
        if len(doc) < 5 and all(token.is_stop or token.is_punct for token in doc if token.text.lower() not in [k.lower() for k in self.generic_praise_keywords + self.generic_criticism_keywords]):
             flags.append({
                "review_id": review_id,
                "flag_type": "unrelated_content",
                "suspicion_score": 0.5,
                "detection_details": {"reason": "Very short review with generic or no relevant content"}
            })

        return flags
