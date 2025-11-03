import json
from datetime import datetime, timedelta

# Placeholder for database connector
class MockDBConnector:
    def get_review_counts_by_product(self, start_date, end_date):
        # Simulate fetching review counts per product within a date range
        # In a real scenario, this would execute a SQL query like:
        # SELECT product_id, COUNT(review_id) AS review_count
        # FROM Reviews
        # WHERE review_date BETWEEN %s AND %s
        # GROUP BY product_id
        print(f"Fetching review counts by product from {start_date} to {end_date}...")
        # Sample data (product_id -> count)
        if (end_date - start_date).days > 1: # Baseline period
            return {
                'P1': 100,
                'P2': 50,
                'P3': 20
            }
        else: # Current window (simulated spike for P1)
            return {
                'P1': 160, # 60% increase
                'P2': 55,
                'P3': 25
            }
            
    def get_reviews_for_product_in_window(self, product_id, start_date, end_date):
        # Simulate fetching actual reviews for a product within a window to flag them
        print(f"Fetching reviews for product {product_id} from {start_date} to {end_date}...")
        # In a real scenario, this would fetch review_ids for flagging
        return [{'review_id': f'SPIKE_REV_{i}'} for i in range(10)] # Dummy review IDs

    def update_review_flag(self, review_id, is_abusive, flagging_reason):
        print(f"Updating review {review_id}: is_abusive={is_abusive}, reason='{flagging_reason}'")
        # In a real scenario:
        # db_connector.execute("UPDATE Reviews SET is_abusive = %s, flagging_reason = %s WHERE review_id = %s", (is_abusive, flagging_reason, review_id))

db_connector = MockDBConnector()

def detect_sudden_spikes(db_connector, config):
    print("Starting sudden spike detection...")
    time_window_hours = config['configuration']['time_window_hours']
    percentage_increase_threshold = config['configuration']['percentage_increase_threshold']
    absolute_increase_threshold = config['configuration']['absolute_increase_threshold']
    baseline_period_days = config['configuration']['baseline_period_days']

    now = datetime.utcnow()
    
    # Define current window
    current_window_end = now
    current_window_start = now - timedelta(hours=time_window_hours)

    # Define baseline window
    baseline_window_end = current_window_start
    baseline_window_start = baseline_window_end - timedelta(days=baseline_period_days)

    # Get review counts for current window
    current_counts = db_connector.get_review_counts_by_product(current_window_start, current_window_end)
    
    # Get review counts for baseline period
    baseline_counts = db_connector.get_review_counts_by_product(baseline_window_start, baseline_window_end)

    flagged_products = set()
    for product_id, current_review_count in current_counts.items():
        baseline_review_count = baseline_counts.get(product_id, 0)
        
        if baseline_review_count == 0 and current_review_count > absolute_increase_threshold:
            # Handle cases where there was no baseline, but a significant number of new reviews
            print(f"Product {product_id}: No baseline reviews, but {current_review_count} reviews in current window (above absolute threshold).")
            flagged_products.add(product_id)
            
        elif baseline_review_count > 0:
            percentage_increase = ((current_review_count - baseline_review_count) / baseline_review_count) * 100
            absolute_increase = current_review_count - baseline_review_count

            if percentage_increase >= percentage_increase_threshold and absolute_increase >= absolute_increase_threshold:
                print(f"Product {product_id}: Spike detected! Current: {current_review_count}, Baseline: {baseline_review_count}, % Increase: {percentage_increase:.2f}%")
                flagged_products.add(product_id)

    flagged_review_count = 0
    for product_id in flagged_products:
        # Fetch reviews for the flagged product in the current window and flag them
        reviews_to_flag = db_connector.get_reviews_for_product_in_window(product_id, current_window_start, current_window_end)
        for review in reviews_to_flag:
            db_connector.update_review_flag(
                review['review_id'],
                True,
                f"Sudden spike in reviews for product {product_id} (Pattern P002)"
            )
            flagged_review_count += 1
            
    print(f"Sudden spike detection complete. Flagged {flagged_review_count} reviews related to {len(flagged_products)} products.")
    return flagged_review_count

# Load configuration for P002 from patterns.json
# In a real system, this would be loaded from the patterns.json file
pattern_config = {
    "pattern_id": "P002",
    "name": "Sudden Spike in Reviews",
    "description": "Identifies unusual surges in the number of reviews for a product within a defined period.",
    "type": "Behavioral",
    "configuration": {
        "time_window_hours": 24,
        "percentage_increase_threshold": 200,
        "absolute_increase_threshold": 50,
        "baseline_period_days": 7
    },
    "severity": "Medium",
    "enabled": True
}

# Example usage (uncomment to run in a Python environment)
# if __name__ == "__main__":
#    detect_sudden_spikes(db_connector, pattern_config)
