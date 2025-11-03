## Database Setup (MVP - PostgreSQL)

This document outlines the steps to set up the PostgreSQL database for the MVP of the Amazon Review Abuse Detection System.

### 1. Prerequisites

*   **Docker** (Recommended for local development) or access to a PostgreSQL server.
*   `psql` command-line client.

### 2. Setup using Docker (Local Development)

1.  **Pull PostgreSQL Docker Image:**
    ```bash
    docker pull postgres:14-alpine
    ```

2.  **Run PostgreSQL Container:**
    ```bash
    docker run --name abuse-detection-db -e POSTGRES_DB=abuse_detection_db -e POSTGRES_USER=abuse_admin -e POSTGRES_PASSWORD=your_secure_password -p 5432:5432 -d postgres:14-alpine
    ```
    *   Replace `your_secure_password` with a strong password.
    *   `abuse-detection-db` is the container name.
    *   `abuse_detection_db` is the database name.
    *   `abuse_admin` is the database user.
    *   `-p 5432:5432` maps the container's port 5432 to your host's port 5432.

3.  **Verify Container Status:**
    ```bash
    docker ps
    ```
    Ensure the `abuse-detection-db` container is running.

### 3. Apply Schema (Create Tables)

1.  **Navigate to the `sql` directory:**
    ```bash
    cd sql
    ```

2.  **Apply the `reviews` table DDL:**
    ```bash
    PGPASSWORD=your_secure_password psql -h localhost -p 5432 -U abuse_admin -d abuse_detection_db -f 001_create_reviews_table.sql
    ```
    *   Replace `your_secure_password` with the password used in step 2.

### 4. Verification

Connect to the database using `psql` and verify the `reviews` table exists:

```bash
PGPASSWORD=your_secure_password psql -h localhost -p 5432 -U abuse_admin -d abuse_detection_db
```

Once connected, run:

```sql
\dt
```

You should see the `reviews` table listed.
