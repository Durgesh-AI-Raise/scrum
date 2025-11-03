
# main.py
# This file serves as a conceptual entry point for the Amazon Review Abuse Detection System.
# In a real-world scenario, this would orchestrate the startup of various microservices
# (Ingestion Service, Review Processing Service, Backend API, etc.) as separate processes
# or deployable units (e.g., Docker containers orchestrated by Kubernetes).

import os
import time
import json
import threading
import bcrypt # For password hashing

# Mock implementations for dependencies (replace with actual client/publisher/manager in production)
class MockMessageQueuePublisher:
    def publish(self, topic, message):
        # print(f"[MQ Publisher] Topic: {topic}, Message: {message[:100]}...")
        pass # In a real system, send to Kafka/SQS

class MockMessageQueueConsumer:
    def __init__(self, topics, group_id, mock_messages=None):
        self.topics = topics
        self.group_id = group_id
        self.mock_messages_queue = mock_messages if mock_messages else []
        self._offset = 0

    def subscribe(self, topics, group_id):
        # print(f"[MQ Consumer] Subscribed to topics: {topics}, Group: {group_id}")
        pass

    def poll(self, timeout_ms=1000):
        if self._offset < len(self.mock_messages_queue):
            message_value = self.mock_messages_queue[self._offset]
            self._offset += 1
            # Mock Kafka message object
            class MockKafkaMessage:
                def value(self): return message_value.encode('utf-8')
                def error(self): return None
            return MockKafkaMessage()
        return None # No message

    def commit(self):
        # print("[MQ Consumer] Committed offset.")
        pass

class MockDatabaseManager:
    def __init__(self):
        self.reviews = {}
        self.bad_actors = {
            "IP_ADDRESS": {"1.2.3.4", "5.6.7.8"},
            "REVIEWER_ID": {"BAD_ACTOR_ID_123", "SUSPICIOUS_REVIEWER_XYZ"}
        }
        self.keywords = [
            {"keyword": r"free product", "category": "INCENTIVIZED", "severity": "HIGH"},
            {"keyword": r"discounted for review", "category": "INCENTIVIZED", "severity": "HIGH"},
            {"keyword": r"happily received", "category": "INCENTIVIZED", "severity": "MEDIUM"},
            {"keyword": r"fake review", "category": "SPAM", "severity": "HIGH"}
        ]
        self.audit_logs = []
        # Pre-hash a password for 'analyst1' (password123)
        self.analyst_users = {
            "analyst1": {"username": "analyst1", "password_hash": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')}
        }

    def insert_review(self, review_data):
        review_id = review_data['review_id']
        self.reviews[review_id] = {**review_data, 'status': 'raw', 'is_flagged': False, 'flagged_reason': None, 'flagged_by': None}
        # print(f"DB: Inserted review {review_id}")

    def update_review(self, review_id, updates):
        if review_id in self.reviews:
            self.reviews[review_id].update(updates)
            # print(f"DB: Updated review {review_id} with {updates}")
        else:
            print(f"DB Error: Review {review_id} not found for update.")

    def get_flagged_reviews(self, status=None, flag_type=None, sort_by='flagged_timestamp', order='desc'):
        filtered = [r for r in self.reviews.values() if r.get('is_flagged', False)]
        if status:
            filtered = [r for r in filtered if r.get('status') == status]
        if flag_type:
            filtered = [r for r in filtered if r.get('flagged_by') and flag_type.lower() in r['flagged_by'].lower()]

        # Simple mock sort
        if sort_by == 'flagged_timestamp':
            filtered.sort(key=lambda x: x.get('flagged_timestamp', ''), reverse=(order == 'desc'))
        elif sort_by == 'overall_rating':
            filtered.sort(key=lambda x: x.get('overall_rating', 0), reverse=(order == 'desc'))

        return list(filtered)

    def insert_audit_log(self, log_data):
        self.audit_logs.append(log_data)
        # print(f"DB: Inserted audit log: {log_data['event_type']}")

    def get_user(self, username):
        return self.analyst_users.get(username)

# --- Ingestion Service (from Task 1.1) ---
class ReviewIngestionService:
    def __init__(self, api_client, mq_publisher, topic_name):
        self.api_client = api_client # Mock API client
        self.mq_publisher = mq_publisher
        self.topic_name = topic_name

    def _fetch_reviews(self):
        print("Ingestion: Fetching new reviews from Amazon source...")
        current_time = int(time.time())
        return [
            {"review_id": f"R{current_time}", "product_id": "B07XXXXXXX", "asin": "B07XXXXXXX", "reviewer_id": "AGSDHWEKJH", "reviewer_name": "John Doe", "review_title": "Great product!", "review_text": "I really enjoyed this product. It works as expected. Highly recommend!", "overall_rating": 5, "review_date": "2023-10-26T10:00:00Z", "purchase_type": "Verified Purchase", "ip_address": "192.168.1.1"},
            {"review_id": f"R{current_time + 1}", "product_id": "B08YYYYYYY", "asin": "B08YYYYYYY", "reviewer_id": "BDGHTRTYUU", "reviewer_name": "Jane Smith", "review_title": "Meh.", "review_text": "It was okay, got it for free product to review. Not worth it.", "overall_rating": 3, "review_date": "2023-10-26T11:00:00Z", "purchase_type": "Not Verified", "ip_address": "1.2.3.4"}, # Bad Actor IP, Keyword
            {"review_id": f"R{current_time + 2}", "product_id": "B09ZZZZZZZ", "asin": "B09ZZZZZZZ", "reviewer_id": "BAD_ACTOR_ID_123", "reviewer_name": "Spammer", "review_title": "Awesome!", "review_text": "Buy this now! discounted for review.", "overall_rating": 5, "review_date": "2023-10-26T12:00:00Z", "purchase_type": "Verified Purchase", "ip_address": "10.0.0.1"} # Bad Actor ID, Keyword
        ]

    def start_ingestion(self, interval_seconds=10):
        while True:
            try:
                reviews = self._fetch_reviews()
                for review in reviews:
                    self.mq_publisher.publish(self.topic_name, json.dumps(review))
                    print(f"Ingestion: Published review {review['review_id']}")
            except Exception as e:
                print(f"Ingestion Error: {e}")
            time.sleep(interval_seconds)

# --- DBPersistence Service (for Reviews - Task 1.3, 1.4) ---
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
class DBPersistenceService:
    def __init__(self, kafka_consumer, db_manager, topic_name, group_id, dlq_publisher, dlq_topic):
        self.kafka_consumer = kafka_consumer
        self.db_manager = db_manager
        self.topic_name = topic_name
        self.group_id = group_id
        self.dlq_publisher = dlq_publisher
        self.dlq_topic = dlq_topic

    def _process_review_message(self, review_data, retry_count=0):
        try:
            self.db_manager.insert_review(review_data)
            print(f"DB_Persistence: Stored review {review_data['review_id']}")
            return True
        except Exception as e:
            print(f"DB_Persistence Error: {e} for review {review_data.get('review_id')}")
            if retry_count < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
                print(f"DB_Persistence: Retrying review {review_data.get('review_id')} (attempt {retry_count + 1})...")
                return self._process_review_message(review_data, retry_count + 1)
            else:
                error_payload = {"original_message": review_data, "error": str(e), "timestamp": time.time(), "service": "db-persistence-service"}
                self.dlq_publisher.publish(self.dlq_topic, json.dumps(error_payload))
                print(f"DB_Persistence: Failed after retries, sent review {review_data.get('review_id')} to DLQ.")
                return False

    def start_consuming(self):
        self.kafka_consumer.subscribe(topics=[self.topic_name], group_id=self.group_id)
        while True:
            message = self.kafka_consumer.poll(timeout_ms=100)
            if message is None:
                continue
            if message.error():
                print(f"DB_Persistence Consumer Error: {message.error()}")
                continue
            
            review_data = json.loads(message.value().decode('utf-8'))
            if self._process_review_message(review_data):
                self.kafka_consumer.commit()
            time.sleep(0.1) # Simulate processing time

# --- Bad Actor Detection Service (Task 2.2) ---
class BadActorDetectionService:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        # In a real app, load from db_manager at init and refresh periodically
        self.cached_bad_ips = db_manager.bad_actors["IP_ADDRESS"]
        self.cached_bad_reviewer_ids = db_manager.bad_actors["REVIEWER_ID"]

    def detect(self, review_data):
        flags = []
        if review_data.get('ip_address') in self.cached_bad_ips:
            flags.append({"type": "BAD_ACTOR_IP", "match": review_data['ip_address'], "severity": "HIGH"})
        if review_data.get('reviewer_id') in self.cached_bad_reviewer_ids:
            flags.append({"type": "BAD_ACTOR_REVIEWER_ID", "match": review_data['reviewer_id'], "severity": "HIGH"})
        return flags

# --- Keyword Detection Service (Task 3.2) ---
class KeywordDetectionService:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        # In a real app, load from db_manager at init and refresh periodically
        self.cached_keywords = db_manager.keywords

    def detect(self, review_text):
        flags = []
        if not review_text: return flags
        normalized_text = review_text.lower()
        for kw_info in self.cached_keywords:
            # Using re.search to find patterns in the text
            if re.search(kw_info['keyword'], normalized_text, re.IGNORECASE):
                flags.append({"type": "KEYWORD_MATCH", "match": kw_info['keyword'], "category": kw_info['category'], "severity": kw_info['severity']})
        return flags

# --- Review Processing Service (Task 2.3, 2.4, 3.3, 3.4) ---
class ReviewProcessingService:
    def __init__(self, consumer, producer, bad_actor_detection_service, keyword_detection_service, db_manager, audit_log_publisher, raw_topic, processed_topic, audit_topic):
        self.consumer = consumer
        self.producer = producer
        self.bad_actor_detection_service = bad_actor_detection_service
        self.keyword_detection_service = keyword_detection_service
        self.db_manager = db_manager
        self.audit_log_publisher = audit_log_publisher
        self.raw_topic = raw_topic
        self.processed_topic = processed_topic
        self.audit_topic = audit_topic

    def start_processing(self):
        self.consumer.subscribe(topics=[self.raw_topic], group_id="detection-processor-group")
        while True:
            message = self.consumer.poll(timeout_ms=100)
            if message is None:
                continue
            if message.error():
                print(f"Review_Processing Consumer Error: {message.error()}")
                continue
            
            review_data = json.loads(message.value().decode('utf-8'))
            review_id = review_data['review_id']
            
            flags = []
            
            # Bad Actor Detection
            bad_actor_flags = self.bad_actor_detection_service.detect(review_data)
            flags.extend(bad_actor_flags)
            
            # Keyword Detection
            keyword_flags = self.keyword_detection_service.detect(review_data.get('review_text', ''))
            flags.extend(keyword_flags)
            
            review_data['detection_flags'] = flags
            
            if flags:
                flagged_reason = ", ".join([f["type"] for f in flags])
                flagged_by_sources = set()
                for f in flags:
                    if f["type"].startswith("BAD_ACTOR"): flagged_by_sources.add("BAD_ACTOR_DETECTION")
                    elif f["type"] == "KEYWORD_MATCH": flagged_by_sources.add("KEYWORD_DETECTION")
                flagged_by = ", ".join(list(flagged_by_sources))

                self.db_manager.update_review(review_id, {
                    'is_flagged': True, 'status': 'flagged', 'flagged_reason': flagged_reason,
                    'flagged_by': flagged_by, 'flagged_timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ")
                })
                print(f"Review_Processing: Flagged review {review_id} by {flagged_by_sources}. Reasons: {flagged_reason}")

                audit_event = {
                    "event_type": "REVIEW_FLAGGED", "review_id": review_id, "source": "REVIEW_PROCESSING_SERVICE",
                    "details": {"flags_triggered": flags, "review_summary": review_data.get('review_title')},
                    "performed_by": "SYSTEM", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                }
                self.audit_log_publisher.publish(self.audit_topic, json.dumps(audit_event))
            
            self.producer.publish(self.processed_topic, json.dumps(review_data))
            # print(f"Review_Processing: Published processed review {review_id} to {self.processed_topic}")
            self.consumer.commit()
            time.sleep(0.1)

# --- Audit Log Persistence Service (Task 6.4) ---
class AuditLogPersistenceService:
    def __init__(self, kafka_consumer, db_manager, topic_name, group_id):
        self.kafka_consumer = kafka_consumer
        self.db_manager = db_manager
        self.topic_name = topic_name
        self.group_id = group_id

    def start_consuming(self):
        self.kafka_consumer.subscribe(topics=[self.topic_name], group_id=self.group_id)
        while True:
            message = self.kafka_consumer.poll(timeout_ms=100)
            if message is None:
                continue
            if message.error():
                print(f"Audit_Log_Persistence Consumer Error: {message.error()}")
                continue
            
            audit_event_data = json.loads(message.value().decode('utf-8'))
            self.db_manager.insert_audit_log(audit_event_data)
            print(f"Audit_Log_Persistence: Stored audit log for review {audit_event_data.get('review_id')}: {audit_event_data['event_type']}")
            self.kafka_consumer.commit()
            time.sleep(0.1)

# --- Backend API (Flask) (Task 4.1, 4.2, 4.3, 4.4, 5.2, 5.3, 6.3) ---
from flask import Flask, jsonify, request, g
from functools import wraps
import re # For keyword service

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a_secret_key_for_dev') # In production, use a strong, random key from env

db_manager_instance = MockDatabaseManager() # Use the global mock DB manager
mq_publisher_instance = MockMessageQueuePublisher() # Use the global mock MQ publisher

# Authentication decorator (Task 4.4)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"message": "Authorization token missing"}), 401
        try:
            token_type, token = auth_header.split(None, 1)
            if token_type.lower() != 'bearer':
                raise ValueError("Invalid token type")
            
            # For MVP, simple API key check
            if token != "fake-analyst-api-key":
                raise ValueError("Invalid API Key")
            
            # In a real system, decode JWT and validate
            g.current_user = "analyst1" # Mock authenticated user
        except Exception as e:
            return jsonify({"message": f"Invalid token: {e}"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    user = db_manager_instance.get_user(username)
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        # In a real app, generate and return a JWT
        return jsonify({"access_token": "fake-analyst-api-key", "username": username}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/api/flagged-reviews', methods=['GET'])
@login_required # Apply authentication
def get_flagged_reviews_api():
    status_filter = request.args.get('status')
    flag_type_filter = request.args.get('flag_type')
    sort_by = request.args.get('sort_by', 'flagged_timestamp')
    order = request.args.get('order', 'desc')
    
    flagged_reviews_data = db_manager_instance.get_flagged_reviews(status_filter, flag_type_filter, sort_by, order)
    return jsonify(flagged_reviews_data)

@app.route('/api/reviews/<string:review_id>/classify', methods=['POST'])
@login_required # Apply authentication
def classify_review_api(review_id):
    classification = request.json.get('classification')
    analyst_username = g.current_user # Get from authenticated user

    if classification not in ['abusive', 'not_abusive', 'needs_investigation']:
        return jsonify({"message": "Invalid classification"}), 400

    try:
        # Task 5.3: Update review status in DB
        db_manager_instance.update_review(review_id, {
            'status': classification,
            'analyst_action_by': analyst_username,
            'analyst_action_timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ")
        })
        print(f"API: Review {review_id} classified as {classification} by {analyst_username}")

        # Task 6.3: Log analyst action to audit trail
        audit_event = {
            "event_type": "REVIEW_CLASSIFIED", "review_id": review_id, "source": "ANALYST_UI",
            "details": {"old_status": "flagged", "new_status": classification}, # Fetch old status from DB for real
            "performed_by": analyst_username, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        mq_publisher_instance.publish("audit-log-topic", json.dumps(audit_event))
        print(f"API: Published audit event for classification of {review_id}")

        return jsonify({"message": "Review classified successfully", "review_id": review_id, "new_status": classification}), 200
    except Exception as e:
        print(f"API Error classifying review {review_id}: {e}")
        return jsonify({"message": "Internal server error"}), 500


# --- Main Application Orchestration ---
if __name__ == "__main__":
    print("Starting Amazon Review Abuse Detection System...")

    # Global mock instances
    mq_publisher = MockMessageQueuePublisher()
    db_manager = db_manager_instance # Use the singleton mock DB manager

    # Mock Kafka topics
    RAW_REVIEWS_TOPIC = "raw-reviews-topic"
    PROCESSED_REVIEWS_TOPIC = "processed-reviews-topic"
    AUDIT_LOG_TOPIC = "audit-log-topic"
    DEAD_LETTER_TOPIC = "dead-letter-topic"

    # Services setup
    # Ingestion Service (Task 1.1)
    ingestion_service = ReviewIngestionService(api_client=None, mq_publisher=mq_publisher, topic_name=RAW_REVIEWS_TOPIC)
    
    # DBPersistence Service for Raw Reviews (Task 1.3, 1.4)
    db_persistence_mock_consumer = MockMessageQueueConsumer(topics=[RAW_REVIEWS_TOPIC], group_id="ingestion-db-saver-group")
    db_persistence_service = DBPersistenceService(kafka_consumer=db_persistence_mock_consumer, db_manager=db_manager,
                                                 topic_name=RAW_REVIEWS_TOPIC, group_id="ingestion-db-saver-group",
                                                 dlq_publisher=mq_publisher, dlq_topic=DEAD_LETTER_TOPIC)
    
    # Detection Services (Task 2.2, 3.2)
    bad_actor_detection_service = BadActorDetectionService(db_manager=db_manager)
    keyword_detection_service = KeywordDetectionService(db_manager=db_manager)

    # Review Processing Service (Task 2.3, 2.4, 3.3, 3.4)
    review_processing_mock_consumer = MockMessageQueueConsumer(topics=[RAW_REVIEWS_TOPIC], group_id="detection-processor-group")
    review_processing_service = ReviewProcessingService(consumer=review_processing_mock_consumer, producer=mq_publisher,
                                                        bad_actor_detection_service=bad_actor_detection_service,
                                                        keyword_detection_service=keyword_detection_service,
                                                        db_manager=db_manager, audit_log_publisher=mq_publisher,
                                                        raw_topic=RAW_REVIEWS_TOPIC, processed_topic=PROCESSED_REVIEWS_TOPIC,
                                                        audit_topic=AUDIT_LOG_TOPIC)

    # Audit Log Persistence Service (Task 6.4)
    audit_log_mock_consumer = MockMessageQueueConsumer(topics=[AUDIT_LOG_TOPIC], group_id="audit-logger-group")
    audit_log_persistence_service = AuditLogPersistenceService(kafka_consumer=audit_log_mock_consumer, db_manager=db_manager,
                                                               topic_name=AUDIT_LOG_TOPIC, group_id="audit-logger-group")

    # Start services in separate threads for simulation
    # In a real deployment, these would be separate processes/containers.
    threading.Thread(target=ingestion_service.start_ingestion, daemon=True).start()
    threading.Thread(target=db_persistence_service.start_consuming, daemon=True).start()
    threading.Thread(target=review_processing_service.start_processing, daemon=True).start()
    threading.Thread(target=audit_log_persistence_service.start_consuming, daemon=True).start()

    print("Background services started. Starting Flask API on port 5000...")
    # Start Flask API (blocking call)
    app.run(port=5000, debug=False, use_reloader=False) # use_reloader=False for thread safety in this simulation
