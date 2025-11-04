
# -*- coding: utf-8 -*-
#
# Sprint 1: Developer Implementation Notes and Core Code Snippets
#
# This file consolidates the implementation plans, data models, architecture,
# assumptions, technical decisions, and key code/pseudocode snippets for Sprint 1
# tasks as requested by the Scrum Master.
#
# GitHub Owner: Durgesh-AI-Raise
# Repository: scrum
#
# --- Data Models ---
#
# 1. Review (PostgreSQL reviews table):
#    - review_id (PK, string)
#    - user_id (string)
#    - product_id (string)
#    - rating (integer)
#    - comment (text)
#    - review_date (timestamp)
#    - source_ip (string)
#    - device_id (string, nullable)
#    - is_flagged (boolean, default false)
#    - flag_reason (string, nullable)
#    - processed_at (timestamp)
#
# 2. Case (PostgreSQL cases table):
#    - case_id (PK, UUID)
#    - review_id (FK to Review, string, UNIQUE)
#    - status (string: 'New', 'Investigating', 'Closed - Abuse', 'Closed - False Positive')
#    - severity (string: 'Low', 'Medium', 'High')
#    - assigned_to (string, nullable, e.g., 'analyst_id')
#    - created_at (timestamp)
#    - updated_at (timestamp)
#    - notes (JSONB array of {timestamp, analyst_id, comment})
#    - tags (JSONB array of strings)
#
# --- SQL Schema for Cases Table (Task 4.2) ---
#
# CREATE TABLE Cases (
#     case_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#     review_id VARCHAR(255) NOT NULL UNIQUE, -- One case per review for now
#     status VARCHAR(50) NOT NULL DEFAULT 'New',
#     severity VARCHAR(50) NOT NULL DEFAULT 'Medium',
#     assigned_to VARCHAR(255), -- ID of the analyst
#     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
#     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
#     notes JSONB DEFAULT '[]'::jsonb, -- Array of {timestamp, analyst_id, comment}
#     tags JSONB DEFAULT '[]'::jsonb, -- Array of strings
#     FOREIGN KEY (review_id) REFERENCES Reviews(review_id)
# );
#
# -- Index for faster lookup by status or assigned_to
# CREATE INDEX idx_cases_status ON Cases (status);
# CREATE INDEX idx_cases_assigned_to ON Cases (assigned_to);
#
# -- Trigger to update 'updated_at' column automatically
# CREATE OR REPLACE FUNCTION update_updated_at_column()
# RETURNS TRIGGER AS $$
# BEGIN
#     NEW.updated_at = NOW();
#     RETURN NEW;
# END;
# $$ LANGUAGE plpgsql;
#
# CREATE TRIGGER update_cases_updated_at
# BEFORE UPDATE ON Cases
# FOR EACH ROW
# EXECUTE FUNCTION update_updated_at_column();


# --- Core Code Snippets (Python Pseudocode) ---

from datetime import datetime, timedelta
import json
from unittest.mock import MagicMock # For testing snippets
import pytest # For testing snippets
from flask import Flask, jsonify, request, abort # For API snippets
import boto3 # For AWS integration snippets
from botocore.exceptions import ClientError # For AWS integration snippets
from uuid import uuid4 # For Case ID generation


# --- User Story: Automated Suspicious Review Flagging ---

# Task 1.1: Design & Implement Review Data Ingestion Pipeline
# db_client is an assumed database interaction object
# send_to_message_queue is an assumed function for publishing messages
class MockDbClient:
    def insert(self, table, data):
        print(f"DB: Inserted into {table}: {data['review_id']}")
    def update_review(self, review_id, updates):
        print(f"DB: Updated review {review_id} with {updates}")
    def get_review_by_id(self, review_id):
        return {"review_id": review_id, "comment": "some comment", "user_id": "u1",
                "review_date": datetime.now(), "source_ip": "1.1.1.1"}
    def get_reviews_paginated(self, filters, page, per_page, order_by):
        return [
            {"review_id": "r1", "user_id": "u1", "product_id": "p1", "rating": 5,
             "comment": "This is a great product! Buy now link: example.com",
             "review_date": datetime.now(), "source_ip": "1.1.1.1", "device_id": None,
             "is_flagged": True, "flag_reason": "Keyword spam detected", "processed_at": datetime.now()}
        ]
    def query_recent_reviews_by_ip_count(self, ip_address, time_window_hours, current_review_id):
        return 0 # Mock for test
    def get_distinct_ips_for_user(self, user_id):
        return ["1.1.1.1"]
    def get_reviews_by_user(self, user_id, exclude_review_id):
        return [{"review_id": "r99", "comment": "Another review by same user"}]
    def get_case_by_review_id(self, review_id):
        return None
    def insert_case(self, case_data):
        return str(uuid4()) # Simulate UUID
    def get_case_by_id(self, case_id):
        return {"case_id": case_id, "review_id": "r100", "status": "New", "severity": "Medium",
                "assigned_to": None, "created_at": datetime.now(), "updated_at": datetime.now(),
                "notes": [], "tags": []}
    def update_case(self, case_id, updates):
        pass # Mock update
    def add_note_to_case(self, case_id, note):
        pass # Mock add note
    def add_tags_to_case(self, case_id, tags):
        pass # Mock add tags


db_client = MockDbClient() # Global mock for snippets


def ingest_review_data(raw_data_payload):
    if not all(k in raw_data_payload for k in ["id", "user", "product", "score", "text", "timestamp", "ip_address"]):
        print("Invalid raw data payload for ingestion.")
        return False

    review_data = {
        "review_id": raw_data_payload["id"],
        "user_id": raw_data_payload["user"],
        "product_id": raw_data_payload["product"],
        "rating": int(raw_data_payload["score"]),
        "comment": raw_data_payload["text"],
        "review_date": datetime.fromisoformat(raw_data_payload["timestamp"].replace('Z', '+00:00')),
        "source_ip": raw_data_payload["ip_address"],
        "device_id": raw_data_payload.get("device_id"),
        "is_flagged": False,
        "flag_reason": None,
        "processed_at": datetime.now()
    }
    db_client.insert("reviews", review_data)
    print(f"Review {review_data['review_id']} inserted into DB.")
    return True


# Task 1.2: Research & Select Initial Suspicious Pattern Detection Algorithms
PATTERN_KEYWORD_SPAM = ["free money", "get rich quick", "buy now link", "discount code"]
PATTERN_SHORT_REVIEW_LENGTH = 15
PATTERN_HIGH_FREQUENCY_IP_THRESHOLD = 5


# Task 1.3: Implement Basic Flagging Logic
def analyze_and_flag_review(review_data):
    flag_reasons = []
    comment_lower = review_data['comment'].lower()

    for keyword in PATTERN_KEYWORD_SPAM:
        if keyword in comment_lower:
            flag_reasons.append("Keyword spam detected")
            break

    if len(review_data['comment']) < PATTERN_SHORT_REVIEW_LENGTH:
        flag_reasons.append("Review too short")

    recent_reviews_from_ip_count = db_client.query_recent_reviews_by_ip_count(
        review_data['source_ip'],
        time_window_hours=1,
        current_review_id=review_data['review_id']
    )
    if recent_reviews_from_ip_count >= PATTERN_HIGH_FREQUENCY_IP_THRESHOLD:
        flag_reasons.append("High frequency reviews from same IP")

    is_flagged = len(flag_reasons) > 0
    final_flag_reason = ", ".join(flag_reasons) if is_flagged else None

    db_client.update_review(
        review_data['review_id'],
        {"is_flagged": is_flagged, "flag_reason": final_flag_reason, "processed_at": datetime.now()}
    )
    print(f"Review {review_data['review_id']} flagged: {is_flagged} with reasons: {final_flag_reason}")
    return is_flagged, final_flag_reason


# Task 1.4: Develop API Endpoint for Flagged Reviews
app = Flask(__name__) # Re-using 'app' for Flask instances for different API routes conceptually


@app.route('/api/v1/flagged_reviews', methods=['GET'])
def get_flagged_reviews():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    filters = {"is_flagged": True}
    flagged_reviews_raw = db_client.get_reviews_paginated(filters=filters, page=page, per_page=per_page, order_by="-review_date")

    serialized_reviews = [
        {
            "review_id": r['review_id'],
            "user_id": r['user_id'],
            "product_id": r['product_id'],
            "rating": r['rating'],
            "comment": r['comment'],
            "review_date": r['review_date'].isoformat(),
            "source_ip": r['source_ip'],
            "is_flagged": r['is_flagged'],
            "flag_reason": r['flag_reason'],
        }
        for r in flagged_reviews_raw
    ]
    return jsonify({"reviews": serialized_reviews, "page": page, "per_page": per_page, "total_items": len(serialized_reviews)})


# Task 1.5: Write Tests for Flagging Logic
# This snippet assumes pytest is configured and analyze_and_flag_review is available
@pytest.fixture
def mock_db_client_flagging():
    mock = MagicMock()
    mock.query_recent_reviews_by_ip_count.return_value = 0
    mock.update_review.return_value = None
    return mock

def test_flagging_keyword_spam(mock_db_client_flagging):
    global db_client # Inject mock
    db_client = mock_db_client_flagging
    review = {
        "review_id": "r1", "user_id": "u1", "product_id": "p1", "rating": 5,
        "comment": "This is a great product! Buy now link: example.com",
        "review_date": datetime.now(), "source_ip": "1.1.1.1", "device_id": None
    }
    is_flagged, reason = analyze_and_flag_review(review)
    assert is_flagged is True
    assert "Keyword spam detected" in reason
    mock_db_client_flagging.update_review.assert_called_once()

# --- User Story: Detailed Abuse Evidence View ---

# Task 3.2: Develop API Endpoint for Detailed Evidence
@app.route('/api/v1/reviews/<string:review_id>/evidence', methods=['GET'])
def get_detailed_evidence(review_id):
    review_data = db_client.get_review_by_id(review_id)
    if not review_data:
        abort(404, description="Review not found")

    related_ips = db_client.get_distinct_ips_for_user(review_data['user_id'])
    other_reviews_by_user = db_client.get_reviews_by_user(review_data['user_id'], exclude_review_id=review_id)

    detailed_evidence = {
        "review_id": review_data['review_id'],
        "user_id": review_data['user_id'],
        "product_id": review_data.get('product_id', 'N/A'),
        "rating": review_data.get('rating', 'N/A'),
        "comment": review_data['comment'],
        "review_date": review_data['review_date'].isoformat(),
        "source_ip": review_data['source_ip'],
        "device_id": review_data.get('device_id'),
        "is_flagged": review_data.get('is_flagged'),
        "flag_reason": review_data.get('flag_reason'),
        "related_ips": related_ips,
        "other_reviews_by_user_count": len(other_reviews_by_user),
        "other_reviews_by_user_snippets": [r['comment'][:50] + '...' for r in other_reviews_by_user[:3]]
    }
    return jsonify(detailed_evidence)


# Task 3.5: Write Tests for Evidence API
@pytest.fixture
def mock_db_client_for_api():
    mock = MagicMock()
    mock.get_review_by_id.return_value = {
        "review_id": "test_r1", "user_id": "test_u1", "product_id": "test_p1",
        "rating": 4, "comment": "Test comment.", "review_date": datetime.now(),
        "source_ip": "1.1.1.1", "device_id": "dev1", "is_flagged": True, "flag_reason": "Test"
    }
    mock.get_distinct_ips_for_user.return_value = ["1.1.1.1"]
    mock.get_reviews_by_user.return_value = []
    return mock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_detailed_evidence_success(client, mock_db_client_for_api):
    global db_client # Inject mock
    db_client = mock_db_client_for_api
    response = client.get('/api/v1/reviews/test_r1/evidence')
    assert response.status_code == 200
    data = response.json
    assert data['review_id'] == "test_r1"
    assert "source_ip" in data
    mock_db_client_for_api.get_review_by_id.assert_called_once_with("test_r1")


# --- User Story: Manual Case Assignment & Status Update ---

# Task 4.3: Develop API Endpoints for Case Updates
def serialize_case_data(case_data):
    if not case_data: return None
    serialized = {k: v for k, v in case_data.items()}
    if 'created_at' in serialized and isinstance(serialized['created_at'], datetime):
        serialized['created_at'] = serialized['created_at'].isoformat()
    if 'updated_at' in serialized and isinstance(serialized['updated_at'], datetime):
        serialized['updated_at'] = serialized['updated_at'].isoformat()
    if 'notes' in serialized and isinstance(serialized['notes'], list):
        serialized['notes'] = [
            {**note, 'timestamp': note['timestamp'].isoformat() if isinstance(note['timestamp'], datetime) else note['timestamp']}
            for note in serialized['notes']
        ]
    return serialized

@app.route('/api/v1/cases', methods=['POST'])
def create_case():
    data = request.get_json()
    review_id = data.get('review_id')
    if not review_id: abort(400, description="review_id required.")

    if db_client.get_case_by_review_id(review_id):
        return jsonify({"message": "Case already exists for this review_id"}), 409

    new_case_data = {
        "review_id": review_id,
        "status": data.get('status', 'New'),
        "severity": data.get('severity', 'Medium'),
        "assigned_to": data.get('assigned_to'),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "notes": [], "tags": []
    }
    case_id = db_client.insert_case(new_case_data)
    new_case_data['case_id'] = case_id
    return jsonify(serialize_case_data(new_case_data)), 201

@app.route('/api/v1/cases/<string:case_id>', methods=['GET'])
def get_case(case_id):
    case_data = db_client.get_case_by_id(case_id)
    if not case_data: abort(404, description="Case not found.")
    return jsonify(serialize_case_data(case_data))

@app.route('/api/v1/cases/<string:case_id>', methods=['PATCH'])
def update_case(case_id):
    data = request.get_json()
    update_fields = {k: v for k, v in data.items() if k in ['status', 'severity', 'assigned_to']}
    if not update_fields: return jsonify({"message": "No valid fields for update"}), 400
    db_client.update_case(case_id, update_fields)
    updated_case = db_client.get_case_by_id(case_id)
    return jsonify(serialize_case_data(updated_case))

@app.route('/api/v1/cases/<string:case_id>/notes', methods=['POST'])
def add_case_note(case_id):
    data = request.get_json()
    note_text = data.get('note')
    analyst_id = data.get('analyst_id', 'system')
    if not note_text: abort(400, description="Note text required.")
    new_note = {"timestamp": datetime.now(), "analyst_id": analyst_id, "comment": note_text}
    db_client.add_note_to_case(case_id, new_note)
    updated_case = db_client.get_case_by_id(case_id)
    return jsonify(serialize_case_data(updated_case))

@app.route('/api/v1/cases/<string:case_id>/tags', methods=['POST'])
def add_case_tags(case_id):
    data = request.get_json()
    tags_to_add = data.get('tags')
    if not isinstance(tags_to_add, list) or not tags_to_add: abort(400, description="Tags must be a non-empty list.")
    db_client.add_tags_to_case(case_id, tags_to_add)
    updated_case = db_client.get_case_by_id(case_id)
    return jsonify(serialize_case_data(updated_case))


# Task 4.5: Write Tests for Case Management APIs
@pytest.fixture
def mock_db_client_for_case_api():
    mock = MagicMock()
    mock.get_case_by_review_id.return_value = None
    mock.get_review_by_id.return_value = {"review_id": "r_new_123"}
    mock.insert_case.return_value = "generated_case_uuid"
    mock.get_case_by_id.return_value = {
        "case_id": "generated_case_uuid", "review_id": "r_new_123",
        "status": "New", "severity": "Medium", "assigned_to": None,
        "created_at": datetime.now(), "updated_at": datetime.now(), "notes": [], "tags": []
    }
    return mock

def test_create_case_success(client, mock_db_client_for_case_api):
    global db_client
    db_client = mock_db_client_for_case_api
    response = client.post('/api/v1/cases', json={'review_id': 'r_new_123', 'status': 'New'})
    assert response.status_code == 201
    data = response.json
    assert data['case_id'] == 'generated_case_uuid'
    mock_db_client_for_case_api.insert_case.assert_called_once()

# --- User Story: Data Integration with Amazon Services ---

# Task 5.3: Develop Secure Integration Modules for Amazon Services
class S3IntegrationModule:
    def __init__(self, region_name='us-east-1'):
        self.s3_client = MagicMock() # Mock boto3 client for snippet
        # self.s3_client = boto3.client('s3', region_name=region_name) # Actual implementation

    def get_json_object(self, bucket_name, key):
        try:
            # response = self.s3_client.get_object(Bucket=bucket_name, Key=key)
            # content = response['Body'].read().decode('utf-8')
            # return json.loads(content)
            print(f"Mock S3: Getting {key} from {bucket_name}")
            return [{"reviewId": "m1", "userId": "u1", "productId": "p1", "starRating": 5, "reviewText": "Mock review", "reviewDate": "2023-01-01T10:00:00Z", "customerIp": "1.2.3.4", "deviceId": "d1"}]
        except ClientError as e:
            print(f"Error getting S3 object {key} from {bucket_name}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from S3 object {key}: {e}")
            return None

    def put_json_object(self, bucket_name, key, data):
        try:
            # json_data = json.dumps(data)
            # self.s3_client.put_object(Bucket=bucket_name, Key=key, Body=json_data, ContentType='application/json')
            print(f"Mock S3: Putting {key} to {bucket_name}")
            return True
        except ClientError as e:
            print(f"Error putting JSON object {key} to {bucket_name}: {e}")
            return False

# Task 5.4: Implement Data Synchronization/ETL Processes
def run_review_etl(s3_bucket_name, s3_object_key, db_client_etl):
    s3_module = S3IntegrationModule()
    raw_reviews = s3_module.get_json_object(s3_bucket_name, s3_object_key)

    if not raw_reviews:
        print(f"No data found in {s3_object_key}.")
        return

    for raw_review in raw_reviews:
        try:
            review_for_db = {
                "review_id": raw_review.get("reviewId"),
                "user_id": raw_review.get("userId"),
                "product_id": raw_review.get("productId"),
                "rating": int(raw_review.get("starRating")),
                "comment": raw_review.get("reviewText"),
                "review_date": datetime.fromisoformat(raw_review.get("reviewDate").replace('Z', '+00:00')),
                "source_ip": raw_review.get("customerIp"),
                "device_id": raw_review.get("deviceId"),
                "is_flagged": False,
                "flag_reason": None,
                "processed_at": datetime.now()
            }
            db_client_etl.insert("reviews", review_for_db)
        except Exception as e:
            print(f"Error processing review {raw_review.get('reviewId')}: {e}")
    print(f"Finished ETL for {s3_object_key}.")


# Task 5.5: Write Integration Tests for Data Connectors
@pytest.fixture
def mock_s3_module_etl():
    mock = MagicMock(spec=S3IntegrationModule)
    mock.get_json_object.return_value = [
        {"reviewId": "m1", "userId": "u1", "productId": "p1", "starRating": 5, "reviewText": "Mock review 1", "reviewDate": "2023-01-01T10:00:00Z", "customerIp": "1.2.3.4", "deviceId": "d1"},
        {"reviewId": "m2", "userId": "u2", "productId": "p2", "starRating": 1, "reviewText": "Mock review 2", "reviewDate": "2023-01-01T11:00:00Z", "customerIp": "5.6.7.8", "deviceId": "d2"}
    ]
    return mock

@pytest.fixture
def mock_db_client_etl():
    mock = MagicMock()
    mock.insert.return_value = None
    return mock

def test_run_review_etl_success(mock_s3_module_etl, mock_db_client_etl):
    # Temporarily replace S3IntegrationModule with our mock for this test
    original_s3_module = globals().get('S3IntegrationModule')
    globals()['S3IntegrationModule'] = lambda: mock_s3_module_etl

    run_review_etl("mock-bucket", "mock-key.json", mock_db_client_etl)

    mock_s3_module_etl.get_json_object.assert_called_once_with("mock-bucket", "mock-key.json")
    assert mock_db_client_etl.insert.call_count == 2

    # Restore original S3IntegrationModule if it was set
    if original_s3_module:
        globals()['S3IntegrationModule'] = original_s3_module

