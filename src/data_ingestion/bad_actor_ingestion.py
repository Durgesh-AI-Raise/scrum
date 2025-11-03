# Pseudocode for a Python data ingestion service
import csv
from datetime import datetime
import uuid

def ingest_bad_actor_data(file_path: str, entity_type: str):
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entity_value = row['entity_value']
            status = row.get('status', 'ACTIVE') # Default status
            reason = row.get('reason', 'Ingested from source list')

            # Validate entity_value based on entity_type (e.g., regex for IP/domain)
            if not validate_entity_value(entity_value, entity_type):
                print(f"Skipping invalid entity: {entity_value} for type {entity_type}")
                continue

            # Connect to database (assuming a DB connection pool is available)
            # cursor = db_connection.cursor()

            # Check if entity already exists
            # existing_bad_actor = cursor.execute(
            #     "SELECT id FROM bad_actors WHERE entity_value = %s AND entity_type = %s",
            #     (entity_value, entity_type)
            # ).fetchone()

            # if existing_bad_actor:
                # Update existing record
                # cursor.execute(
                #     """
                #     UPDATE bad_actors
                #     SET status = %s, reason = %s, updated_at = %s
                #     WHERE id = %s
                #     """,
                #     (status, reason, datetime.now(), existing_bad_actor['id'])
                # )
                # print(f"Updated bad actor: {entity_value}")
            # else:
                # Insert new record
                # new_id = uuid.uuid4()
                # cursor.execute(
                #     """
                #     INSERT INTO bad_actors (id, entity_type, entity_value, status, reason, created_at, updated_at)
                #     VALUES (%s, %s, %s, %s, %s, %s, %s)
                #     """,
                #     (new_id, entity_type, entity_value, status, reason, datetime.now(), datetime.now())
                # )
                # print(f"Inserted new bad actor: {entity_value}")

            # db_connection.commit()
    print(f"Ingestion complete for {file_path}")

def validate_entity_value(value: str, entity_type: str) -> bool:
    # Basic validation placeholders
    if entity_type == 'IP':
        # return is_valid_ip(value)
        return True # Placeholder
    elif entity_type == 'DOMAIN':
        # return is_valid_domain(value)
        return True # Placeholder
    elif entity_type == 'ACCOUNT':
        # return is_valid_account_id(value)
        return True # Placeholder
    return False

# Example usage:
# ingest_bad_actor_data('blacklist_ips.csv', 'IP')
# ingest_bad_actor_data('suspended_accounts.csv', 'ACCOUNT')