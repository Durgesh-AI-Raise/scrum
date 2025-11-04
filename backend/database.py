
import json
import datetime
import uuid

# --- Database Simulation (for demonstration purposes) ---
# In a real application, this would interact with a PostgreSQL database
# using a library like psycopg2.

_mock_db_reviews = {}
_mock_db_moderator_action_log = {}
_mock_db_reviewer_history = {}

def execute_db_query(query, params=None):
    """
    Simulates database query execution.
    For this demo, it directly manipulates the in-memory mock_db.
    """
    print(f"DEBUG: Executing query: {query} with params: {params}")
    
    # Simple simulation logic for specific queries
    if "INSERT INTO reviews" in query:
        review_id = str(uuid.uuid4())
        _mock_db_reviews[review_id] = {
            "id": review_id,
            "product_id": params[0],
            "reviewer_id": params[1],
            "review_content": params[2],
            "ip_address": params[3],
            "review_content_hash": params[4],
            "submission_timestamp": datetime.datetime.now(datetime.timezone.utc),
            "is_flagged": False,
            "flagging_reason": None,
            "severity_score": 0,
            "is_abusive": False,
            "is_legitimate": False,
            "moderator_id": None,
            "moderator_action_timestamp": None,
        }
        return {"id": review_id}
    elif "SELECT review_content_hash, ARRAY_AGG(id) FROM reviews" in query:
        # Simplified simulation for detection queries
        # This would be a complex SQL query in real life
        results = {}
        for review_id, review in _mock_db_reviews.items():
            if review["submission_timestamp"] >= datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24):
                hash_key = review["review_content_hash"]
                if hash_key not in results:
                    results[hash_key] = []
                results[hash_key].append(review_id)
        # Filter for more than 5 distinct IPs per hash (simplified)
        filtered_results = {k: v for k, v in results.items() if len(v) > 5}
        return [(k, v) for k,v in filtered_results.items()]
    elif "SELECT product_id, ARRAY_AGG(id) FROM reviews" in query:
        results = {}
        for review_id, review in _mock_db_reviews.items():
            if review["submission_timestamp"] >= datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1):
                product_key = review["product_id"]
                if product_key not in results:
                    results[product_key] = []
                results[product_key].append(review_id)
        # Filter for more than 10 reviews per product (simplified)
        filtered_results = {k: v for k, v in results.items() if len(v) > 10}
        return [(k, v) for k,v in filtered_results.items()]
    elif "SELECT flagging_reason FROM reviews WHERE id = %s" in query:
        review = _mock_db_reviews.get(params[0])
        return [[review["flagging_reason"]]] if review else [[None]]
    elif "UPDATE reviews SET is_flagged = TRUE" in query:
        review_id = params[2]
        if review_id in _mock_db_reviews:
            _mock_db_reviews[review_id]["is_flagged"] = True
            _mock_db_reviews[review_id]["flagging_reason"] = json.loads(params[0])
            _mock_db_reviews[review_id]["severity_score"] = max(_mock_db_reviews[review_id]["severity_score"], params[1])
            return True
        return False
    elif "SELECT id, product_id, reviewer_id, flagging_reason, severity_score, submission_timestamp FROM reviews WHERE is_flagged = TRUE" in query:
        flagged = []
        for review_id, review in _mock_db_reviews.items():
            if review["is_flagged"] and not review["is_abusive"] and not review["is_legitimate"]:
                flagged.append((review["id"], review["product_id"], review["reviewer_id"], review["flagging_reason"], review["severity_score"], review["submission_timestamp"]))
        # Simulate sorting and pagination
        flagged.sort(key=lambda x: (x[4], x[5]), reverse=True) # severity DESC, timestamp DESC
        per_page = params[0]
        offset = params[1]
        return flagged[offset:offset + per_page]
    elif "SELECT id, product_id, reviewer_id, review_content, submission_timestamp, ip_address, flagging_reason, severity_score, is_abusive, is_legitimate FROM reviews WHERE id = %s" in query:
        review = _mock_db_reviews.get(str(params[0]))
        if review:
            return [(review["id"], review["product_id"], review["reviewer_id"], review["review_content"], review["submission_timestamp"], review["ip_address"], review["flagging_reason"], review["severity_score"], review["is_abusive"], review["is_legitimate"])]
        return []
    elif "UPDATE reviews SET is_abusive = TRUE" in query:
        review_id = params[1]
        if review_id in _mock_db_reviews:
            _mock_db_reviews[review_id]["is_abusive"] = True
            _mock_db_reviews[review_id]["is_flagged"] = False
            _mock_db_reviews[review_id]["moderator_id"] = params[0]
            _mock_db_reviews[review_id]["moderator_action_timestamp"] = datetime.datetime.now(datetime.timezone.utc)
            return True
        return False
    elif "UPDATE reviews SET is_legitimate = TRUE" in query:
        review_id = params[1]
        if review_id in _mock_db_reviews:
            _mock_db_reviews[review_id]["is_legitimate"] = True
            _mock_db_reviews[review_id]["is_flagged"] = False
            _mock_db_reviews[review_id]["moderator_id"] = params[0]
            _mock_db_reviews[review_id]["moderator_action_timestamp"] = datetime.datetime.now(datetime.timezone.utc)
            return True
        return False
    elif "INSERT INTO moderator_action_log" in query:
        log_id = str(uuid.uuid4())
        _mock_db_moderator_action_log[log_id] = {
            "id": log_id,
            "review_id": params[0],
            "moderator_id": params[1],
            "action_type": params[2],
            "action_timestamp": datetime.datetime.now(datetime.timezone.utc),
            "reason": params[3],
        }
        return True
    elif "SELECT reviewer_id FROM reviews WHERE id = %s" in query:
        review = _mock_db_reviews.get(params[0])
        return [[review["reviewer_id"]]] if review else []
    elif "INSERT INTO reviewer_history" in query or "ON CONFLICT (reviewer_id) DO UPDATE" in query:
        reviewer_id = params[0]
        current_history = _mock_db_reviewer_history.get(reviewer_id, {
            "reviewer_id": reviewer_id,
            "total_reviews_submitted": 0,
            "total_flagged_reviews": 0,
            "total_abusive_reviews": 0,
            "last_flagged_timestamp": None,
            "last_abusive_timestamp": None
        })

        if "total_reviews_submitted = reviewer_history.total_reviews_submitted + 1" in query and "total_abusive_reviews = reviewer_history.total_abusive_reviews + 1" in query:
            # Abusive action
            current_history["total_reviews_submitted"] += 1
            current_history["total_flagged_reviews"] += 1 # Assume if abusive, it was also flagged
            current_history["total_abusive_reviews"] += 1
            current_history["last_abusive_timestamp"] = datetime.datetime.now(datetime.timezone.utc)
        elif "total_reviews_submitted = reviewer_history.total_reviews_submitted + 1" in query and "GREATEST(0, reviewer_history.total_flagged_reviews - 1)" in query:
            # Legitimate action (unflagging)
            current_history["total_reviews_submitted"] += 1
            current_history["total_flagged_reviews"] = max(0, current_history["total_flagged_reviews"] - 1)
        elif "total_reviews_submitted = reviewer_history.total_reviews_submitted + 1" in query and "last_flagged_timestamp = NOW()" in query:
            # Initial flagging or review submission
            current_history["total_reviews_submitted"] += 1
            current_history["total_flagged_reviews"] += 1
            current_history["last_flagged_timestamp"] = datetime.datetime.now(datetime.timezone.utc)
        else: # Initial insert if no conflict or just submission
             current_history["total_reviews_submitted"] += 1 # Default increment for any review
        
        _mock_db_reviewer_history[reviewer_id] = current_history
        return True
    elif "SELECT total_reviews_submitted, total_flagged_reviews, total_abusive_reviews, last_flagged_timestamp, last_abusive_timestamp FROM reviewer_history WHERE reviewer_id = %s" in query:
        history = _mock_db_reviewer_history.get(params[0])
        if history:
            return [(history["total_reviews_submitted"], history["total_flagged_reviews"], history["total_abusive_reviews"], history["last_flagged_timestamp"], history["last_abusive_timestamp"])]
        return []
    
    print(f"WARNING: Unhandled query in mock_db: {query}")
    return []

# --- Public API for Database Interactions ---

def insert_review(product_id, reviewer_id, review_content, ip_address, review_content_hash):
    db_query = "INSERT INTO reviews (product_id, reviewer_id, review_content, ip_address, review_content_hash) VALUES (%s, %s, %s, %s, %s);"
    return execute_db_query(db_query, (product_id, reviewer_id, review_content, ip_address, review_content_hash))

def get_flagging_reasons(review_id):
    result = execute_db_query("SELECT flagging_reason FROM reviews WHERE id = %s;", (review_id,))
    return result[0][0] if result and result[0] else None

def update_review_flag_status(review_id, flagging_reason_json, severity_score):
    db_query = "UPDATE reviews SET is_flagged = TRUE, flagging_reason = %s, severity_score = GREATEST(severity_score, %s) WHERE id = %s;"
    execute_db_query(db_query, (json.dumps(flagging_reason_json), severity_score, review_id))

def get_flagged_reviews_from_db(per_page, offset):
    db_query = "SELECT id, product_id, reviewer_id, flagging_reason, severity_score, submission_timestamp FROM reviews WHERE is_flagged = TRUE ORDER BY severity_score DESC, submission_timestamp DESC LIMIT %s OFFSET %s;"
    return execute_db_query(db_query, (per_page, offset))

def get_review_details_from_db(review_id):
    db_query = "SELECT id, product_id, reviewer_id, review_content, submission_timestamp, ip_address, flagging_reason, severity_score, is_abusive, is_legitimate FROM reviews WHERE id = %s;"
    return execute_db_query(db_query, (review_id,))

def mark_review_abusive_in_db(review_id, moderator_id):
    db_query = "UPDATE reviews SET is_abusive = TRUE, is_flagged = FALSE, moderator_id = %s, moderator_action_timestamp = NOW() WHERE id = %s;"
    execute_db_query(db_query, (moderator_id, review_id))

def mark_review_legitimate_in_db(review_id, moderator_id):
    db_query = "UPDATE reviews SET is_legitimate = TRUE, is_flagged = FALSE, moderator_id = %s, moderator_action_timestamp = NOW() WHERE id = %s;"
    execute_db_query(db_query, (moderator_id, review_id))

def log_moderator_action(review_id, moderator_id, action_type, reason=None):
    db_query = "INSERT INTO moderator_action_log (review_id, moderator_id, action_type, reason) VALUES (%s, %s, %s, %s);"
    execute_db_query(db_query, (review_id, moderator_id, action_type, reason))

def get_reviewer_id_for_review(review_id):
    result = execute_db_query("SELECT reviewer_id FROM reviews WHERE id = %s;", (review_id,))
    return result[0][0] if result else None

def get_reviewer_history_from_db(reviewer_id):
    db_query = "SELECT total_reviews_submitted, total_flagged_reviews, total_abusive_reviews, last_flagged_timestamp, last_abusive_timestamp FROM reviewer_history WHERE reviewer_id = %s;"
    return execute_db_query(db_query, (reviewer_id,))
