
# services/review_velocity_service.py

from datetime import datetime, timedelta
import psycopg2 # Assuming PostgreSQL driver
import os

class ReviewVelocityService:
    def __init__(self, db_connection_string: str):
        self.conn = psycopg2.connect(db_connection_string)

    def get_review_velocity(self, product_id: str, time_window_minutes: int) -> int:
        """
        Calculates the number of reviews for a product within a specified time window.
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=time_window_minutes)

        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM reviews WHERE product_id = %s AND submission_timestamp BETWEEN %s AND %s;",
                (product_id, start_time, end_time)
            )
            count = cursor.fetchone()[0]
        finally:
            cursor.close()
        return count

    def close_connection(self):
        self.conn.close()

# Example usage (for testing purposes, not part of the service itself)
if __name__ == '__main__':
    # Placeholder for actual DB connection string from environment variables or config
    DB_CONNECTION_STRING = os.getenv("DATABASE_URL", "dbname=reviews_db user=user password=pass host=localhost")
    service = ReviewVelocityService(DB_CONNECTION_STRING)
    # Example: Get velocity for 'prod123' in the last 60 minutes
    # velocity = service.get_review_velocity('prod123', 60)
    # print(f"Review velocity for prod123 in last 60 mins: {velocity}")
    service.close_connection()
