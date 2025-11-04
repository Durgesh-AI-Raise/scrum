# Suspicious Reviewer Behavior Patterns (MVP)

This document outlines the initial set of suspicious reviewer behavior patterns identified for detection.

## 1. Sudden Burst of Positive Reviews
**Description:** A reviewer account suddenly posts a significantly higher number of positive reviews (e.g., 4-5 stars) within a short timeframe (e.g., 2-7 days) compared to their historical average, often for a diverse or unrelated set of products.
**Heuristic Definition:**
*   `N` reviews in `X` days, where `N` exceeds a reviewer's historical average by `Y` standard deviations.
*   `P%` of these `N` reviews are positive (e.g., >= 4 stars).
*   Optional: High diversity in product categories reviewed.

## 2. Rapid-Fire Reviews Across Unrelated Products
**Description:** A reviewer posts multiple reviews for different products within a very short time window (e.g., minutes to an hour), especially if these products are from disparate categories, suggesting automated or unnatural behavior.
**Heuristic Definition:**
*   `M` distinct products reviewed within `T` minutes.
*   Optional: Products belong to `C` or more different categories.

## 3. Repetitive Review Content by Different Accounts (Basic Heuristic)
**Description:** While detailed content anomaly detection is a separate task, a basic reviewer behavior pattern could involve multiple distinct reviewer accounts posting highly similar reviews for the *same product* within a close time window, indicating coordinated activity.
**Heuristic Definition:**
*   For a given `product_id`, `X` distinct reviewers post reviews within `Y` hours.
*   A significant percentage (`Z%`) of these reviews have high text similarity (to be more precisely defined in Content Anomaly task).
*   *Note: This pattern will heavily leverage and be refined by the "Review Content Anomaly" detection module.*
