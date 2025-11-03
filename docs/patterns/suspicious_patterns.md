# Suspicious Review Patterns

This document outlines the initial set of suspicious patterns identified for automatic detection of review abuse. These patterns will inform the development of feature extraction and rule-based flagging within the ARIG system.

## Defined Patterns:

1.  **Unusual Reviewer Velocity:**
    *   **Description:** A single reviewer submitting an unusually high number of reviews within a short period (e.g., more than X reviews in Y days). This could indicate bot activity or a paid reviewer.
    *   **Indicators:** Number of reviews by reviewer in last 24h, 7 days, 30 days.

2.  **New Account Rapid Reviews:**
    *   **Description:** A newly created reviewer account (e.g., less than Z days old) submitting multiple reviews, especially with high velocity.
    *   **Indicators:** Reviewer account creation date, number of reviews by new accounts.

3.  **Unusual Rating Distribution:**
    *   **Description:** A reviewer consistently giving extreme ratings (e.g., all 5-star or all 1-star) across diverse products, or a rating that significantly deviates from the product's average rating without substantial justification in text.
    *   **Indicators:** Reviewer's average rating, standard deviation of reviewer's ratings, deviation from product's average rating.

4.  **Duplicate or Highly Similar Reviews:**
    *   **Description:** The same or nearly identical review text submitted by one or multiple reviewers for different products, or even the same product.
    *   **Indicators:** Review text similarity, existence of exact duplicate review text.

5.  **Reviewer-Product Affinity Imbalance:**
    *   **Description:** A reviewer exclusively or overwhelmingly reviewing products from a single seller or brand, potentially indicating collusion. (Note: This might be harder to implement in Sprint 1 due to data needs but is a consideration for future).

## Next Steps:

These definitions will be used to develop concrete features (Task 1.3) and rules (Task 1.4) in the ARIG system. Thresholds (X, Y, Z values) will be determined during implementation and can be made configurable.
