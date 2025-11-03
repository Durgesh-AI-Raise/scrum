### Task 1.4: Set up database/storage for review data

**Objective:** Provision and configure the PostgreSQL database instance for ARIS review data.

**Steps:**

1.  **Provision PostgreSQL Instance:**
    *   Choose a cloud provider (e.g., AWS RDS, Google Cloud SQL, Azure Database for PostgreSQL).
    *   Create a new PostgreSQL database instance with the following recommended configurations:
        *   **Database Name:** `aris_db`
        *   **Master Username:** `aris_admin`
        *   **Master Password:** Generate a strong, secure password and store it in a secure secret management system.
        *   **Instance Class:** Start with a `db.t3.medium` (AWS RDS equivalent) or similar for development/testing.
        *   **Allocated Storage:** 100 GB (can be scaled later).
        *   **Engine Version:** PostgreSQL 14 or later.
        *   **VPC/Network Configuration:** Ensure the database is accessible from the ARIS application services (e.g., within the same VPC, correct security group rules).
        *   **Public Accessibility:** Set to `No` for production environments. For initial testing, it might be `Yes` but ensure strict IP whitelisting.

2.  **Connect to the Database:**
    *   Once the instance is available, obtain its endpoint (host address) and port.
    *   Use a PostgreSQL client (e.g., `psql`, DBeaver, pgAdmin) to connect using the `aris_admin` credentials.
    
    ```bash
    psql -h <DB_HOST_ENDPOINT> -p 5432 -U aris_admin -d aris_db
    ```

3.  **Execute Data Model DDL:**
    *   Execute the SQL DDL script located at `docs/db_schema/task_1.1_review_data_model.sql` to create all necessary tables, enums, and indexes.
    
    ```bash
    psql -h <DB_HOST_ENDPOINT> -p 5432 -U aris_admin -d aris_db -f docs/db_schema/task_1.1_review_data_model.sql
    ```
    *   Verify that `products`, `reviewers`, and `reviews` tables have been created successfully.

4.  **Configure Application Access:**
    *   Ensure that the ARIS application services can connect to this database using the appropriate credentials and network configuration. Database connection strings should be stored as environment variables or secrets.
