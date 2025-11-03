import json
import os

def validate_review_data(filepath):
    """Performs basic structural and type validation on a review data file."""
    print(f"Validating file: {filepath}")
    is_valid = True
    required_fields = ["review_id", "product_id", "reviewer_id", "rating", "text", "review_date"]
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"  Error: Root element is not a list in {filepath}")
            is_valid = False
            return is_valid

        for i, review in enumerate(data):
            if not isinstance(review, dict):
                print(f"  Error: Review at index {i} is not a dictionary.")
                is_valid = False
                continue

            for field in required_fields:
                if field not in review:
                    print(f"  Error: Review ID '{(review.get('review_id', 'N/A'))}' (index {i}) missing required field: '{field}'")
                    is_valid = False
            
            # Basic type checks (can be expanded)
            if 'rating' in review and not isinstance(review['rating'], int):
                print(f"  Warning: Review ID '{(review.get('review_id', 'N/A'))}' (index {i}) has non-integer rating.")
            if 'text' in review and not isinstance(review['text'], str):
                print(f"  Warning: Review ID '{(review.get('review_id', 'N/A'))}' (index {i}) has non-string text.")

    except json.JSONDecodeError as e:
        print(f"  Error: Invalid JSON format in {filepath}: {e}")
        is_valid = False
    except FileNotFoundError:
        print(f"  Error: File not found: {filepath}")
        is_valid = False
    
    if is_valid:
        print(f"  Validation successful for {filepath}")
    else:
        print(f"  Validation failed for {filepath}")
    return is_valid

def run_data_validation(directory="raw_data"):
    """Runs validation on all JSON files in the specified directory."""
    print(f"Starting data validation for directory: {directory}")
    all_valid = True
    if not os.path.exists(directory):
        print(f"  Error: Directory '{directory}' not found.")
        return False
        
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            if not validate_review_data(filepath):
                all_valid = False
    
    if all_valid:
        print("All ingested data files passed basic validation.")
    else:
        print("Some ingested data files failed validation. Check logs for details.")
    return all_valid

# Example usage (commented out as it will be called by the pipeline)
# if __name__ == "__main__":
#     # Create a dummy valid file for testing
#     os.makedirs("raw_data", exist_ok=True)
#     dummy_data_valid = [
#         {"review_id": "R100", "product_id": "P1", "reviewer_id": "U1", "rating": 5, "title": "Good", "text": "This is great.", "review_date": "2023-10-01T10:00:00Z"},
#         {"review_id": "R101", "product_id": "P2", "reviewer_id": "U2", "rating": 4, "title": "Okay", "text": "It's fine.", "review_date": "2023-10-02T11:00:00Z"}
#     ]
#     with open("raw_data/test_valid.json", "w") as f:
#         json.dump(dummy_data_valid, f, indent=2)

#     # Create a dummy invalid file (missing field) for testing
#     dummy_data_invalid = [
#         {"review_id": "R200", "product_id": "P3", "reviewer_id": "U3", "rating": 3, "title": "Bad", "review_date": "2023-10-03T12:00:00Z"} # Missing 'text'
#     ]
#     with open("raw_data/test_invalid.json", "w") as f:
#         json.dump(dummy_data_invalid, f, indent=2)

#     print("Running validation example:")
#     run_data_validation()