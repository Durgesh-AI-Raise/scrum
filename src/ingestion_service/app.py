# Pseudocode for Ingestion Service Endpoint (Python Flask/FastAPI)
from flask import Flask, request, jsonify
from kafka import KafkaProducer
import json
import uuid
from datetime import datetime

app = Flask(__name__)
producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'], # Or Kinesis/Pub/Sub client
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.route('/reviews', methods=['POST'])
def submit_review():
    try:
        review_data = request.get_json()
        if not review_data:
            return jsonify({"error": "No data provided"}), 400

        # Add internal metadata
        review_data['review_id'] = str(uuid.uuid4())
        review_data['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        review_data['is_flagged'] = False
        review_data['flag_reason'] = []

        # Publish to Kafka topic
        producer.send('raw_reviews', review_data)
        producer.flush() # Ensure message is sent

        return jsonify({"message": "Review submitted successfully", "review_id": review_data['review_id']}), 201
    except Exception as e:
        # Log error
        print(f"Error processing review: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
