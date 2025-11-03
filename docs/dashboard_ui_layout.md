# Dashboard UI/UX Layout - Conceptual Design

## Overview

The dashboard will be a single-page application focused on presenting key review abuse metrics at a glance. It will be responsive and designed for Trust & Safety Analysts.

## Key Sections and Components:

1.  **Header/Navigation:**
    *   Application title: "Review Abuse Tracking System"
    *   Basic navigation links (e.g., Dashboard, Flagged Reviews - to be implemented in later sprints).

2.  **Metric Cards (Top Row):**
    *   **Total Flagged Reviews:** A large number indicating the cumulative count.
    *   **Flagged Last 24 Hours:** Number of reviews flagged in the past day.
    *   **Active Campaigns (Placeholder):** Will initially show "N/A" or "0" until campaign identification is more robust.
    *   Each card will have a descriptive title and the numerical value.

3.  **Flagged Reviews Trend (Main Chart):**
    *   **Type:** Line Chart
    *   **X-axis:** Time (e.g., Last 7 days, Last 30 days)
    *   **Y-axis:** Number of Flagged Reviews
    *   **Interaction:** Potentially date range selector.

4.  **Flagging Reason Breakdown (Secondary Chart):**
    *   **Type:** Bar Chart or Pie Chart
    *   **Data:** Distribution of flagged reviews by primary reason (e.g., "Keyword Match - Spam", "Keyword Match - Promotional").

5.  **Recent Flagged Reviews (Table):**
    *   **Columns:** Review ID, Product ID (ASIN), Reviewer ID, Date Flagged, Primary Reason.
    *   **Action:** Clickable row/link to view detailed review information (Task 4.1-4.4).
    *   **Pagination/Scrolling:** For large datasets.

## Wireframe Sketch (Text-based Representation):

```
+-----------------------------------------------------------------------+
| Header: Review Abuse Tracking System                                  |
+-----------------------------------------------------------------------+
| [ Total Flagged ]   [ Flagged Last 24h ]  [ Active Campaigns ]        |
| [     12,345    ]   [         123      ]  [          0       ]        |
+-----------------------------------------------------------------------+
|                                                                       |
|             Flagged Reviews Over Time (Line Chart)                    |
|             [------------------------------------]                    |
|             [             (Graph Area)           ]                    |
|             [------------------------------------]                    |
|                                                                       |
+-----------------------------------------------------------------------+
|               Flagging Reason Breakdown               Recent Flagged Reviews  |
|               [-----------------------]               [-----------------------]|
|               [   (Bar/Pie Chart)     ]               [ ReviewID | ProductID..]|
|               [-----------------------]               [-----------------------]|
|                                                       [ Row 1 (clickable)    ]|
|                                                       [ Row 2 (clickable)    ]|
|                                                       [ Row 3 (clickable)    ]|
|                                                       [ ...                  ]|
+-----------------------------------------------------------------------+
```

## Technical Notes:
*   Frontend framework: React.
*   Charting library: To be determined (e.g., Chart.js, Recharts).
*   Data will be fetched asynchronously from backend APIs.
