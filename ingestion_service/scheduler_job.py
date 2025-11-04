# This would typically be a wrapper around the ingestion_service.py
# import ingestion_service
# from config import get_monitored_product_ids

def run_daily_ingestion():
    """
    Scheduled job to run review ingestion for all monitored products.
    This function would be triggered by a cron scheduler or similar.
    """
    print("Starting daily review ingestion job...")
    monitored_product_ids = ["B07XYZ123", "B01ABC456", "B08DEF789"] # get_monitored_product_ids()

    for product_id in monitored_product_ids:
        try:
            # ingestion_service.ingest_product_reviews(product_id)
            print(f"Triggered ingestion for product: {product_id}")
        except Exception as e:
            print(f"Failed to ingest reviews for {product_id}: {e}")

    print("Daily review ingestion job completed.")

if __name__ == "__main__":
    run_daily_ingestion()
