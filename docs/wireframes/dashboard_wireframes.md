# Dashboard UI/UX Wireframes - MVP

## Overview
This document outlines the basic wireframes for the Amazon Review Integrity System's analyst dashboard. The goal is to provide Trust & Safety Analysts with a clear and efficient way to view and prioritize potentially abusive reviews.

## Key Sections:

1.  **Header:**
    *   Logo (left)
    *   System Name: "Amazon Review Integrity" (center)
    *   User/Profile (right, e.g., "Analyst Name | Logout")

2.  **Dashboard Title:** "Abusive Reviews Dashboard"

3.  **Filter & Search Bar:**
    *   Input field for `Search (Review ID, Reviewer ID, Product ASIN)`
    *   Dropdown for `Filter by Detection Type (e.g., Similar Content, Suspicious Activity)`
    *   Dropdown for `Filter by Status (e.g., Pending, Investigating, Actioned)`
    *   `Apply Filters` button

4.  **Reviews Listing Area:**
    *   **Display Mode:** Table (for clarity and scannability)
    *   **Columns:**
        *   `Review ID` (clickable to view detailed profile)
        *   `Reviewer Name` (clickable to view reviewer profile)
        *   `Product ASIN`
        *   `Review Content Snippet` (first ~100 characters)
        *   `Rating` (1-5 stars)
        *   `Detection Type` (e.g., Similar Content, Suspicious Activity)
        *   `Similarity Score` (numeric, e.g., 0.95)
        *   `Status` (e.g., Pending, Investigating, Actioned)
        *   `Actions` (e.g., a "View Details" button/link to the full review/reviewer profile)

5.  **Pagination:** Standard pagination controls below the table (e.g., `Previous | 1 2 3 ... 10 | Next`).

## User Flow:

1.  Analyst lands on the dashboard.
2.  Sees a list of potentially abusive reviews.
3.  Can use filters to narrow down the list.
4.  Clicks on a `Review ID` or `View Details` to see more specific information about the review and its detection.
5.  Clicks on a `Reviewer Name` to see the detailed reviewer profile.

## Mockup Sketch (Conceptual Layout):

```
+---------------------------------------------------------------------------------------+
| [LOGO]                 AMAZON REVIEW INTEGRITY                 [Analyst Name | Logout]|
+---------------------------------------------------------------------------------------+
|                                                                                       |
|  -----------------------------------------------------------------------------------  |
| |                    Abusive Reviews Dashboard                                      | |
|  -----------------------------------------------------------------------------------  |
|                                                                                       |
|  [Search Input] [Filter: Detection Type ▼] [Filter: Status ▼] [Apply Filters Button]  |
|                                                                                       |
|  +---------------------------------------------------------------------------------+  |
|  | Review ID | Reviewer Name | Product ASIN | Review Content Snippet | ... | Actions |  |
|  +-----------+---------------+--------------+------------------------+-----+---------+  |
|  | REV001    | John Doe      | B001         | "Great product, but..."| ... | View    |  |
|  | REV002    | Jane Smith    | B002         | "Avoid at all costs..."| ... | View    |  |
|  | ...       | ...           | ...          | ...                    | ... | ...     |  |
|  +---------------------------------------------------------------------------------+  |
|                                                                                       |
|  [ < Prev | 1 | 2 | 3 | Next > ]                                                       |
|                                                                                       |
+---------------------------------------------------------------------------------------+
```
