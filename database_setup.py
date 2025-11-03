# database_setup.py

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configuration
DB_HOST = "localhost"
DB_NAME = "review_abuse_db"
DB_USER = "user"
DB_PASSWORD = "password"

def setup_database():
    # Connect to default database to create the new database
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Create database if it doesn't exist
        try:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
            print(f"Database '{DB_NAME}' created successfully.")
        except psycopg2.errors.DuplicateDatabase:
            print(f"Database '{DB_NAME}' already exists.")
        except Exception as e:
            print(f"Error creating database: {e}")

        cur.close()
        conn.close()

        # Connect to the newly created/existing database to create tables
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()

        # Create reviews table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id VARCHAR(255) PRIMARY KEY,
            product_id VARCHAR(255) NOT NULL,
            reviewer_id VARCHAR(255) NOT NULL,
            rating INT NOT NULL,
            review_title TEXT,
            review_text TEXT NOT NULL,
            review_date TIMESTAMP NOT NULL,
            verified_purchase BOOLEAN,
            helpful_votes INT,
            product_category VARCHAR(255),
            product_brand VARCHAR(255),
            review_source VARCHAR(50),
            ingestion_timestamp TIMESTAMP NOT NULL,
            is_flagged BOOLEAN DEFAULT FALSE,
            flagging_reason TEXT[] DEFAULT '{}',
            flagging_timestamp TIMESTAMP,
            abuse_score DECIMAL(5,2) DEFAULT 0.0,
            current_status VARCHAR(50) DEFAULT 'Pending'
        );
        """)
        print("Table 'reviews' created or already exists.")

        # Create indexes for faster lookups
        cur.execute("CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews (product_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_reviews_reviewer_id ON reviews (reviewer_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_reviews_is_flagged_status ON reviews (is_flagged, current_status);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_reviews_abuse_score ON reviews (abuse_score DESC);")
        print("Indexes created or already exist.")

        # Placeholder tables for reviewers and products (can be populated via aggregation later)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reviewers (
            reviewer_id VARCHAR(255) PRIMARY KEY,
            total_reviews INT DEFAULT 0,
            average_rating DECIMAL(2,1),
            first_review_date TIMESTAMP,
            last_review_date TIMESTAMP,
            flagged_review_count INT DEFAULT 0
        );
        """)
        print("Table 'reviewers' created or already exists.")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id VARCHAR(255) PRIMARY KEY,
            product_name TEXT,
            category VARCHAR(255),
            brand VARCHAR(255),
            average_rating DECIMAL(2,1),
            total_reviews INT DEFAULT 0,
            flagged_review_count INT DEFAULT 0
        );
        """)
        print("Table 'products' created or already exists.")


        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    setup_database()
