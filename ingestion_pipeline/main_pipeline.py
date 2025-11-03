import json
import logging
from typing import Dict, Optional

from ingestion_pipeline.data_models import ReviewData
# Assuming nlp_module and database_module will be created later
# from nlp_module import process_review_nlp
# from database_module import save_flagged_review

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_review_data(raw_data: Dict) -> Optional[ReviewData]:
    """
    Parses raw review data dictionary into a ReviewData object.
    Includes basic validation.
    """
    try:
        review_id = raw_data.get('review_id')
        product_id = raw_data.get('product_id')
        reviewer_id = raw_data.get('reviewer_id')
        review_text = raw_data.get('review_text')
        star_rating = raw_data.get('star_rating')
        review_timestamp = raw_data.get('review_timestamp')

        # Basic validation for essential fields
        if not all([review_id, product_id, reviewer_id, review_text, star_rating, review_timestamp]):
            logger.warning(f"Skipping review due to missing essential fields: {raw_data.get('review_id', 'N/A')}")
            return None
        
        # Ensure star_rating is an integer
        try:
            star_rating = int(star_rating)
        except (ValueError, TypeError):
            logger.warning(f"Invalid star_rating for review {review_id}. Expected int, got {star_rating}. Skipping.")
            return None

        return ReviewData(
            review_id=review_id,
            product_id=product_id,
            reviewer_id=reviewer_id,
            review_text=review_text,
            star_rating=star_rating,
            review_timestamp=review_timestamp,
            raw_data=raw_data # Store raw data for debugging
        )
    except Exception as e:
        logger.error(f"Error parsing review data: {e}. Raw data: {raw_data.get('review_id', 'N/A')}")
        return None

def full_ingestion_pipeline(raw_review_data: Dict):
    """
    Orchestrates the full ingestion, processing, and storage pipeline for a single review.
    """
    logger.info(f"Starting full ingestion pipeline for review: {raw_review_data.get('review_id', 'N/A')}")
    
    # 1. Parse Review Data (Task 1.3)
    parsed_review = parse_review_data(raw_review_data)
    if not parsed_review:
        logger.warning(f"Failed to parse review, skipping further processing for: {raw_review_data.get('review_id', 'N/A')}")
        return

    # 2. NLP Processing (User Story 2 - Tasks 2.2, 2.3, 2.4, 2.5)
    try:
        # Placeholder for NLP processing - will be implemented in NLP module
        # processed_review = process_review_nlp(parsed_review)
        # For now, just pass the parsed review
        processed_review = parsed_review 
        logger.info(f"Review {processed_review.review_id} processed by NLP (placeholder).")
    except Exception as e:
        logger.error(f"Error during NLP processing for review {parsed_review.review_id}: {e}")
        # Decide whether to halt or continue with partial data
        processed_review = parsed_review # Continue with parsed data if NLP fails

    # 3. Persist Flagged Data (User Story 3 - Task 3.3)
    # This step will only save if patterns are detected or it's always desired to store
    # For this sprint, we'll assume we save all processed reviews, even if no patterns are found,
    # as the goal is to "persist all flagged review abuse data".
    # The condition `if processed_review.detected_patterns:` will be added later when NLP is real.
    try:
        # Placeholder for database storage - will be implemented in database module
        # save_flagged_review(processed_review)
        logger.info(f"Review {processed_review.review_id} persisted to database (placeholder).")
    except Exception as e:
        logger.error(f"Error persisting review {processed_review.review_id} to database: {e}")
    
    logger.info(f"Finished full ingestion pipeline for review: {raw_review_data.get('review_id', 'N/A')}")
