# Dashboard UI Layout and Components Design

## Overview
The dashboard will provide Trust & Safety Analysts with a centralized view of potential review abuse alerts. It will be an interactive single-page application.

## Key Sections:
1.  **Header:**
    *   Application Title / Logo
    *   User Profile / Logout
    *   Global Search (future)

2.  **Sidebar (Left Panel):**
    *   **Filter Controls:**
        *   Severity (High, Medium, Low) - Multi-select checkbox/dropdown
        *   Alert Type (Behavioral, Text) - Multi-select checkbox/dropdown
        *   Status (New, Triaged, Investigating) - Multi-select checkbox/dropdown
        *   Date Range Picker
    *   **Action Buttons:**
        *   "Apply Filters"
        *   "Clear Filters"

3.  **Main Content Area (Alerts List):**
    *   **Alerts Table:**
        *   Columns: Alert ID, Severity, Type, Subtype, Reviewer ID, Product ASIN, Timestamp, Status, Summary.
        *   Clickable rows to open `AlertDetailPanel`.
    *   **Pagination Controls:**
        *   Show X of Y results
        *   Previous/Next page buttons
        *   Page number selector

4.  **Alert Detail Panel (Right Panel - Collapsible/Expandable):**
    *   Displays comprehensive details of a selected alert.
    *   Sections:
        *   **Alert Summary:** ID, Type, Subtype, Severity, Status, Timestamp.
        *   **Review Details:** Review ID, Star Rating, Review Title, Review Text (truncated with "Read More"), Verified Purchase, Marketplace.
        *   **Reviewer Details (Summary):** Reviewer ID, Total Reviews, Average Rating (overall).
        *   **Product Details (Summary):** Product ASIN, Product Name (future), Average Rating (product).
        *   **Detection Specifics:** Detailed reasons for the alert (e.g., "Burst: 10 reviews in 5 min", "Keywords: 'free product', 'gift card'").
        *   **Action Buttons:** "Mark as Triaged", "Escalate", "False Positive".

## Component List:
*   `DashboardLayout` (main container)
*   `Header`
*   `Sidebar`
*   `FilterControls`
*   `AlertsTable`
*   `AlertsTableRow`
*   `PaginationControls`
*   `AlertDetailPanel`
*   `SeverityIndicator`
*   `StatusBadge`
