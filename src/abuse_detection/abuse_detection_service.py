
import json
import os
import datetime
from collections import defaultdict

from src.abuse_detection.rules import (
    rule_new_account_multiple_reviews,
    rule_high_volume_new_product_reviews,
    rule_identical_content_across_products
)

class AbuseDetectionService:
    def __init__(self, input_file: str = 'data/enriched_reviews.json', output_file: str = 'data/flagged_reviews.json'):
        self.input_file = input_file
        self.output_file = output_file
        self.rules = [
            ("New Account Multiple Reviews", rule_new_account_multiple_reviews),
            ("High Volume New Product Reviews", rule_high_volume_new_product_reviews),
            ("Identical Content Across Products", rule_identical_content_across_products)
        ]

    def _load_enriched_reviews(self) -> list:
        """Loads enriched review data from the input file."""
        reviews = []
        if os.path.exists(self.input_file):
            with open(self.input_file, 'r') as f:
                try:
                    reviews = json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: {self.input_file} is empty or malformed. No reviews to process.")
                    reviews = []
        else:
            print(f"Error: Input file {self.input_file} not found. Cannot perform abuse detection.")
        return reviews

    def _save_flagged_reviews(self, flagged_reviews_data: list):
        """Saves the processed flagged review data to the output file."""
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w') as f:
            json.dump(flagged_reviews_data, f, indent=4)
        print(f"[{datetime.datetime.now().isoformat()}] Flagging complete. Total flagged reviews saved to {self.output_file}.")

    def detect_abuse(self):
        """
        Runs all defined abuse detection rules on the enriched review data
        and flags suspicious reviews.
        """
        print(f"[{datetime.datetime.now().isoformat()}] Starting abuse detection process...")
        enriched_reviews = self._load_enriched_reviews()
        if not enriched_reviews:
            print(f"[{datetime.datetime.now().isoformat()}] No enriched reviews found to process. Exiting abuse detection.")
            return

        # Initialize all reviews as not suspicious
        processed_reviews_map = {review['review_id']: {**review, 'is_suspicious': False, 'suspicion_reasons': []} for review in enriched_reviews}

        for rule_name, rule_function in self.rules:
            print(f"[{datetime.datetime.now().isoformat()}] Applying rule: {rule_name}...")
            flagged_by_rule = rule_function(enriched_reviews)
            for flagged_review in flagged_by_rule:
                review_id = flagged_review['review_id']
                if review_id in processed_reviews_map:
                    processed_review = processed_reviews_map[review_id]
                    processed_review['is_suspicious'] = True
                    if rule_name not in processed_review['suspicion_reasons']:
                        processed_review['suspicion_reasons'].append(rule_name)
                    processed_reviews_map[review_id] = processed_review # Update the map

        final_flagged_output = list(processed_reviews_map.values())
        self._save_flagged_reviews(final_flagged_output)
        print(f"[{datetime.datetime.now().isoformat()}] Abuse detection process finished. {sum(1 for r in final_flagged_output if r['is_suspicious'])} reviews flagged as suspicious.")


if __name__ == '__main__':
    # Ensure raw_reviews.json and enriched_reviews.json exist for this to run
    # Example workflow:
    # from src.data_ingestion.data_ingestion import ingest_review_data
    # from src.data_ingestion.data_enrichment import enrich_review_data
    #
    # ingest_review_data()
    # enrich_review_data()
    
    abuse_detector = AbuseDetectionService()
    abuse_detector.detect_abuse()
