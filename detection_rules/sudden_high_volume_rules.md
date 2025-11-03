## Sudden High Volume Review Detection Rules

**Purpose:** To identify suspicious reviewer patterns characterized by an unusually rapid submission of reviews.

**Assumptions & Technical Decisions:**

*   Detection will primarily rely on global, static thresholds rather than individual reviewer historical baselines for this initial sprint.
*   A 24-hour sliding window will be used for recent review activity analysis.
*   The `review_data_persistence_service` (MongoDB) will be queried for review counts.

### Rule 1: Recent Review Burst

*   **Description:** Flag a reviewer if they submit a significantly high number of reviews within a short, recent period, indicating a potential concentrated burst of activity.
*   **Condition:** A reviewer has posted `X` or more reviews within the last `Y` hours.
*   **Initial Thresholds:**
    *   `X` (Minimum number of reviews): **5**
    *   `Y` (Time window in hours): **24**
*   **Rationale:** A sudden surge of 5 or more reviews within a single day from any account could indicate automated behavior or an organized attempt to manipulate ratings.

### Rule 2: New Reviewer High Activity

*   **Description:** Flag a reviewer who has a relatively new account (e.g., less than a week old) and immediately exhibits a high volume of reviews. This targets newly created accounts potentially used for fraudulent purposes.
*   **Condition:** A reviewer's account age is less than `A` days AND they have posted `B` or more reviews within the last `C` hours.
*   **Initial Thresholds:**
    *   `A` (Maximum account age in days): **7**
    *   `B` (Minimum number of reviews): **3**
    *   `C` (Time window in hours): **24**
*   **Rationale:** New accounts with an immediate, high volume of reviews are often indicative of bot activity or fake accounts. These thresholds are set low to broadly capture such suspicious behavior from nascent accounts.
