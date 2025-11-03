from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from .text_analyzer import TextAnalyzer
from .db_manager import DatabaseManager
from .config import DB_CONFIG, THRESHOLDS # Assuming a config.py for settings

app = FastAPI(title="Text Abuse Detection Service")
analyzer = TextAnalyzer()
db_manager = DatabaseManager(DB_CONFIG)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReviewInput(BaseModel):
    review_id: str
    review_text: str
    product_id: str
    user_id: str

class FlagOutput(BaseModel):
    flag_id: int
    review_id: str
    flag_type: str
    suspicion_score: float
    detection_details: Dict[str, Any]

@app.post("/analyze-review", response_model=List[FlagOutput])
async def analyze_review(review: ReviewInput):
    """
    Analyzes a review for suspicious text patterns and flags it if abuse is detected.
    """
    logger.info(f"Received review for analysis: {review.review_id}")
    try:
        flags = analyzer.analyze(review.review_id, review.review_text)
        
        # Filter flags that exceed the general suspicion threshold
        triggered_flags = [f for f in flags if f['suspicion_score'] >= THRESHOLDS['overall_suspicion']]

        if triggered_flags:
            inserted_flags = []
            for flag in triggered_flags:
                inserted_flag_id = db_manager.insert_text_abuse_flag(
                    review_id=flag['review_id'],
                    flag_type=flag['flag_type'],
                    suspicion_score=flag['suspicion_score'],
                    detection_details=flag['detection_details']
                )
                inserted_flags.append(
                    FlagOutput(
                        flag_id=inserted_flag_id,
                        review_id=flag['review_id'],
                        flag_type=flag['flag_type'],
                        suspicion_score=flag['suspicion_score'],
                        detection_details=flag['detection_details']
                    )
                )
            logger.info(f"Flagged review {review.review_id} with {len(inserted_flags)} abuse flags.")
            return inserted_flags
        else:
            logger.info(f"No suspicious patterns found for review {review.review_id} above threshold.")
            return []
    except Exception as e:
        logger.error(f"Error analyzing review {review.review_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during review analysis.")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
