from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson.json_util import dumps # For handling ObjectId and datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# MongoDB Configuration
MONGO_URI = 'mongodb://localhost:27017/' # Replace with actual MongoDB URI
MONGO_DB = 'aris'
PROCESSED_REVIEWS_COLLECTION = 'processed_reviews'

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
processed_reviews_collection = db[PROCESSED_REVIEWS_COLLECTION]

@app.route('/reviews', methods=['GET'])
def get_reviews():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    skip = (page - 1) * limit

    try:
        reviews_cursor = processed_reviews_collection.find().skip(skip).limit(limit)
        reviews = json.loads(dumps(list(reviews_cursor))) # Convert ObjectId and datetime to string/ISO format
        
        logger.info(f"Retrieved {len(reviews)} processed reviews for page {page}")
        return jsonify(reviews)
    except Exception as e:
        logger.error(f"Error fetching reviews: {e}")
        return jsonify({"message": "Internal server error"}), 500

@app.route('/reviews/<string:review_id>', methods=['GET'])
def get_review_by_id(review_id):
    try:
        # Assuming 'reviewId' is a field in your document, not the MongoDB _id
        review = processed_reviews_collection.find_one({'reviewId': review_id})
        if review:
            logger.info(f"Retrieved review with reviewId: {review_id}")
            return jsonify(json.loads(dumps(review))) # Convert ObjectId and datetime
        else:
            logger.warning(f"Review with reviewId: {review_id} not found")
            return jsonify({"message": "Review not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching review {review_id}: {e}")
        return jsonify({"message": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
