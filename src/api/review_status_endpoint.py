from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Mock Database for Flagged Reviews ---
# In a real application, this would be an ORM or direct database calls
# to a NoSQL or SQL database.
flagged_reviews_db = {
    "review_123": {
        "text": "This product broke after one use.",
        "rating": 1,
        "timestamp": "2023-10-26T10:00:00Z",
        "reviewer_id": "user_A",
        "product_id": "prod_X",
        "status": "Under Investigation",  # Initial status
        "flag_reason": "Rapid review burst"
    },
    "review_456": {
        "text": "Amazing! Five stars!",
        "rating": 5,
        "timestamp": "2023-10-25T14:30:00Z",
        "reviewer_id": "user_B",
        "product_id": "prod_Y",
        "status": "Under Investigation",
        "flag_reason": "Identical review text"
    }
}

# --- Allowed Statuses ---
ALLOWED_STATUSES = ["Confirmed Abuse", "False Positive", "Under Investigation"]

# --- API Endpoint to Update Review Status ---
@app.route("/reviews/<string:review_id>/status", methods=["PATCH"])
def update_review_status(review_id):
    """
    Updates the status of a flagged review.
    Expected request body: {"status": "New Status Value"}
    """
    # 1. Check if the review exists
    if review_id not in flagged_reviews_db:
        print(f"ERROR: Review with ID '{review_id}' not found.")
        return jsonify({"error": f"Review with ID '{review_id}' not found"}), 404

    # 2. Parse request body
    try:
        data = request.get_json()
    except Exception as e:
        print(f"ERROR: Failed to parse JSON body: {e}")
        return jsonify({"error": "Invalid JSON in request body"}), 400

    if not data or "status" not in data:
        print("ERROR: Missing 'status' field in request body.")
        return jsonify({"error": "Missing 'status' in request body"}), 400

    new_status = data["status"]

    # 3. Validate new status
    if new_status not in ALLOWED_STATUSES:
        print(f"ERROR: Invalid status provided: '{new_status}'. Allowed: {ALLOWED_STATUSES}")
        return jsonify(
            {"error": f"Invalid status provided. Allowed statuses are: {', '.join(ALLOWED_STATUSES)}"}
        ), 400

    # 4. Update the status in the mock database
    old_status = flagged_reviews_db[review_id]["status"]
    flagged_reviews_db[review_id]["status"] = new_status
    print(f"INFO: Review '{review_id}' status updated from '{old_status}' to '{new_status}'.")

    # 5. Return success response
    return jsonify({
        "message": "Review status updated successfully",
        "review_id": review_id,
        "old_status": old_status,
        "new_status": new_status
    }), 200

# --- Example of how to run the Flask app (for development) ---
if __name__ == "__main__":
    # In a production environment, use a production-ready WSGI server
    # e.g., gunicorn -w 4 -b 0.0.0.0:5000 app:app
    app.run(debug=True, port=5000)
