import json
import time
import random
import logging
from ingestion_pipeline.main_pipeline import full_ingestion_pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_stream(data_source_file="mock_amazon_reviews.jsonl", delay_seconds=1):
    """
    Simulates a real-time stream by reading reviews from a JSONL file
    and passing them to the full ingestion pipeline.
    """
    logger.info(f"Starting simulated review stream from {data_source_file}")
    try:
        with open(data_source_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    raw_review_data = json.loads(line.strip())
                    logger.info(f"Ingesting review from mock stream (line {line_num}): {raw_review_data.get('review_id', 'N/A')}")
                    
                    # Pass the raw data (dict) to the main pipeline
                    full_ingestion_pipeline(raw_review_data)
                    
                    time.sleep(delay_seconds + random.uniform(-0.5, 0.5)) # Simulate variable arrival
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON on line {line_num}: {e} in line: {line.strip()[:100]}...")
                except Exception as e:
                    logger.error(f"An unexpected error occurred during stream processing on line {line_num}: {e}. Data: {line.strip()[:100]}...")
    except FileNotFoundError:
        logger.error(f"Mock data source file not found: {data_source_file}")
    except Exception as e:
        logger.error(f"An error occurred while opening or reading the data source file: {e}")

if __name__ == "__main__":
    # Example mock_amazon_reviews.jsonl content (create this file in the root directory):
    # {"review_id": "R1", "product_id": "P1", "reviewer_id": "U1", "review_text": "This product is absolutely amazing! I love it so much. Amazing! Amazing!", "star_rating": 5, "review_timestamp": "2023-10-26T10:00:00Z"}
    # {"review_id": "R2", "product_id": "P2", "reviewer_id": "U2", "review_text": "Terrible quality, broke after one use. So bad, so bad. Horrible.", "star_rating": 1, "review_timestamp": "2023-10-26T10:01:00Z"}
    # {"review_id": "R3", "product_id": "P3", "reviewer_id": "U3", "review_text": "It's okay. Nothing special.", "star_rating": 3, "review_timestamp": "2023-10-26T10:02:00Z"}
    # {"review_id": "R4", "product_id": "P1", "reviewer_id": "U4", "review_text": "I bought this for my friend, and she absolutely adores it. Best gift ever!", "star_rating": 5, "review_timestamp": "2023-10-26T10:03:00Z"}
    # {"review_id": "R5", "product_id": "P5", "reviewer_id": "U5", "review_text": "This is simply the worst. I repeat, the worst! Absolutely terrible, terrible, terrible.", "star_rating": 1, "review_timestamp": "2023-10-26T10:04:00Z"}
    simulate_stream()
