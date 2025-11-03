
# src/backend/review_abuse_detection_api.py

# This code would be deployed as an AWS Lambda function behind API Gateway.

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
import os
from datetime import datetime
import uuid
import json 
from typing import List, Optional

# --- DB Configuration (Pseudocode/Placeholder) ---
# In a real application, you would use SQLAlchemy or another ORM
# to interact with your PostgreSQL database.
# For this example, direct database interactions are mocked.

# Example Pydantic model for a database entry if we were using an ORM
class FlaggedReviewDBModel(BaseModel):
    flag_id: str
    review_id: str
    ml_model_id: str
    prediction_score: float
    flagged_timestamp: str # ISO format
    status: str
    abuse_categories: List[str] = []
    analyst_notes: Optional[str] = None
    analyst_id: Optional[str] = None
    categorization_timestamp: Optional[str] = None


# --- ML Model Inference (SageMaker Runtime) ---
# Ensure SAGEMAKER_ENDPOINT_NAME is set in your environment variables.
SAGEMAKER_ENDPOINT_NAME = os.getenv("SAGEMAKER_ENDPOINT_NAME", "your-sagemaker-abuse-detection-endpoint")
SAGEMAKER_RUNTIME = boto3.client("sagemaker-runtime")

app = FastAPI(title="Review Abuse Detection Service")

class ReviewInput(BaseModel):
    """
    Input model for new reviews to be flagged.
    """
    review_id: str
    review_text: str
    # Add other relevant features for ML model if needed, e.g., reviewer_history_score, product_metadata

def preprocess_review_for_ml(review_text: str) -> list:
    """
    Placeholder for review preprocessing logic.
    This function must exactly match the preprocessing steps used during model training
    to ensure consistent feature engineering for inference.
    """
    # In a real scenario, this would involve:
    # 1. Cleaning text (lowercase, remove punctuation, stopwords, special characters)
    # 2. Tokenization (splitting text into words or subword units)
    # 3. Vectorization (e.g., TF-IDF, Word2Vec, BERT embeddings)
    # 4. Potentially adding other numerical features derived from metadata.
    
    # Mocking a simple feature vector for demonstration purposes.
    # The length of this vector must match the ML model's expected input dimension.
    # Example features: text length, exclamation marks count, presence of 'spam' keyword.
    mock_feature_vector = [
        len(review_text), 
        review_text.count("!"), 
        1 if "spam" in review_text.lower() else 0,
        1 if "free" in review_text.lower() else 0,
        1 if "gift" in review_text.lower() else 0
    ]
    
    # Pad or truncate to a fixed length (e.g., 10 features) if the model expects it.
    fixed_feature_length = 10
    if len(mock_feature_vector) < fixed_feature_length:
        mock_feature_vector.extend([0.0] * (fixed_feature_length - len(mock_feature_vector)))
    return mock_feature_vector[:fixed_feature_length] # Ensure it's exactly fixed_feature_length


@app.post("/flag_review")
async def flag_review(review_input: ReviewInput):
    """
    Endpoint to receive a new review, preprocess it, get an ML prediction,
    and flag the review if the prediction score exceeds a predefined threshold.
    """
    # 1. Preprocess the review text
    processed_features = preprocess_review_for_ml(review_input.review_text)

    # 2. Invoke SageMaker Endpoint for real-time prediction
    try:
        # SageMaker expects a specific input format (e.g., CSV, JSON).
        # Adjust 'ContentType' and 'Body' based on your model's input_fn.
        # This example assumes a JSON input format for a TF serving-like model.
        payload = json.dumps({"instances": [processed_features]})
        
        response = SAGEMAKER_RUNTIME.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT_NAME,
            ContentType="application/json",
            Body=payload
        )
        
        result = json.loads(response["Body"].read().decode())
        # Assuming SageMaker returns a list of probabilities for binary classification
        # where result['predictions'][0][1] is the probability of the positive class (abuse).
        prediction_score = result["predictions"][0][1]
        
    except Exception as e:
        print(f"Error invoking SageMaker endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"ML prediction failed: {str(e)}")

    # 3. Determine if review is flagged based on a configurable threshold
    FLAGGING_THRESHOLD = float(os.getenv("FLAGGING_THRESHOLD", "0.7")) # Default to 0.7 if not set
    is_abusive = prediction_score >= FLAGGING_THRESHOLD
    
    # Prepare details for the flagged review record
    flag_details = FlaggedReviewDBModel(
        flag_id=str(uuid.uuid4()), # Generate a unique ID for this flag
        review_id=review_input.review_id,
        ml_model_id="abuse-detector-v1.0", # Identifier for the ML model used
        prediction_score=prediction_score,
        flagged_timestamp=datetime.utcnow().isoformat(),
        status="PENDING_REVIEW" # Initial status for analyst review
    )

    if is_abusive:
        # 4. Store flagged review metadata in the database (mocked for this snippet)
        try:
            # In a real application, you would use your ORM to save this object:
            # db_session.add(flag_details)
            # db_session.commit()
            print(f"Review {review_input.review_id} FLAGGED. Prediction Score: {prediction_score:.2f}, Flag ID: {flag_details.flag_id}")
            # Log the flagged event
        except Exception as e:
            # db_session.rollback()
            print(f"Failed to store flagged review {review_input.review_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to store flagged review: {str(e)}")
    else:
        print(f"Review {review_input.review_id} NOT FLAGGED. Prediction Score: {prediction_score:.2f}")
        # Optionally, you might log non-flagged reviews for auditing/analysis
        # flag_details.status = "NOT_FLAGGED" 
        flag_details = None # Do not return flag_details if not flagged

    return {
        "review_id": review_input.review_id,
        "is_abusive": is_abusive,
        "prediction_score": prediction_score,
        "flag_details": flag_details.dict() if flag_details else None # Return details only if flagged
    }

# To run this FastAPI app locally for testing (install uvicorn: pip install uvicorn)
# uvicorn review_abuse_detection_api:app --reload --port 8000

# For production deployment, this would be wrapped by AWS Lambda and API Gateway.
# The 'boto3' client will use IAM roles from the Lambda execution environment.
