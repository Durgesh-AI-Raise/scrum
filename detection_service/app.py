from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# Mock detection function (to be replaced with ML model)
def detect_abuse(review_text):
    abuse_keywords = ['spam', 'scam', 'fake']
    score = 0.0
    for word in abuse_keywords:
        if word in review_text.lower():
            score += 0.5
    # Randomness for demo
    score += random.uniform(0, 0.5)
    abusive_flag = score > 0.7
    return {'abusiveScore': score, 'abusiveFlag': abusive_flag, 'details': 'Keyword match plus ML model score'}

@app.route('/detect', methods=['POST'])
def detect():
    data = request.json
    review_text = data.get('reviewText', '')
    result = detect_abuse(review_text)
    result['reviewId'] = data.get('reviewId')
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
