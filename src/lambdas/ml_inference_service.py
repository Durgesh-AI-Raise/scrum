
import json
import boto3
import os

SM_ENDPOINT_NAME = os.environ.get("SM_ENDPOINT_NAME", "your-ml-inference-endpoint") # Env var for endpoint name
sagemaker_runtime = boto3.client("sagemaker-runtime")

def extract_ml_features(review):
    """Extracts features from the review object for ML inference."""
    # This must exactly match the feature engineering used for model training
    review_text = review.get("review_text", "")
    return {
        "review_text_length": len(review_text),
        "num_capital_letters": sum(1 for c in review_text if c.isupper()),
        "punctuation_ratio": sum(1 for c in review_text if c in ".,!?;:") / (len(review_text) or 1),
        "rating": review.get("rating", 0)
        # Add other features as per your model's training
    }

def lambda_handler(event, context):
    processed_records = []
    for record_body in event: # Receives review objects after spam detection
        review = record_body

        try:
            features_for_ml = extract_ml_features(review)
            response = sagemaker_runtime.invoke_endpoint(
                EndpointName=SM_ENDPOINT_NAME,
                ContentType="application/json",
                Accept="application/json",
                Body=json.dumps(features_for_ml)
            )
            inference_result = json.loads(response['Body'].read().decode())
            
            if inference_result.get("ml_suspicious_flag") == 1:
                existing_flags = review.get("detection_flags", [])
                review["detection_flags"] = list(set(existing_flags + ["ML_SUSPICIOUS_PATTERN"]))
            
            review["ml_anomaly_score"] = inference_result.get("ml_anomaly_score")

        except Exception as e:
            print(f"ML inference failed for review {review.get('review_id')}: {e}")
            # Log error, potentially add a "ML_INFERENCE_ERROR" flag or send alert
        
        processed_records.append(review)
    return processed_records
