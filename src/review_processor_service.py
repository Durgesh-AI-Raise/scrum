from flask import Flask, request, jsonify
import re
from collections import Counter

app = Flask(__name__)

# Pseudocode for NLP analysis
def analyze_text_for_suspicious_patterns(text):
    patterns = []
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower) # Simple word tokenization

    # Rule 1: Check for repeated phrases (simple word repetition for now)
    word_counts = Counter(words)
    for word, count in word_counts.items():
        if count >= 4 and len(word) > 2: # Word repeated 4 or more times
            patterns.append(f"repeated_phrase:{word}")

    # Rule 2: Check for unnaturally short/long reviews
    if len(words) < 8 and len(words) > 0: # Very short reviews
        patterns.append("unnaturally_short_review")
    elif len(words) > 400: # Very long reviews, potentially spam
        patterns.append("unnaturally_long_review")

    # Rule 3: Check for excessive capitalization
    if sum(1 for c in text if c.isupper()) / max(1, len(text)) > 0.4 and len(text) > 20:
        patterns.append("excessive_capitalization")

    # Rule 4: Check for excessive punctuation (e.g., !!!, ???)
    if re.search(r'[!?.]{3,}|[!?. ]{2,}[!?. ]{2,}', text):
        patterns.append("excessive_punctuation")

    return patterns

@app.route('/process_review', methods=['POST'])
def process_review():
    data = request.json
    review_id = data.get('review_id')
    review_text = data.get('review_text')

    if not review_id or not review_text:
        return jsonify({"error": "Missing review_id or review_text"}), 400

    detected_patterns = analyze_text_for_suspicious_patterns(review_text)
    # A very basic initial score contribution based on number of patterns
    # Each pattern contributes a fixed amount, could be more sophisticated
    initial_score_contribution = len(detected_patterns) * 15

    return jsonify({
        "review_id": review_id,
        "detected_patterns": detected_patterns,
        "initial_score_contribution": initial_score_contribution
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
