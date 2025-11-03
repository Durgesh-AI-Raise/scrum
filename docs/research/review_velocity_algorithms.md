# Research: Review Velocity Detection Algorithms

## Overview
This document summarizes research into algorithms for detecting anomalies in review velocity, aiming to identify potential review bombing or manipulation. The focus is on methods suitable for time-series data, considering interpretability and computational efficiency.

## Candidate Algorithms

### 1. Statistical Methods

#### a. Moving Averages (Simple Moving Average - SMA, Exponential Moving Average - EMA)
*   **Concept:** Smooths out short-term fluctuations to highlight longer-term trends. Anomalies are data points significantly outside a certain band around the moving average.
*   **Pros:** Easy to understand and implement. EMA is more responsive to recent changes.
*   **Cons:** Lagging indicator, might not detect sudden, sharp spikes immediately. Requires tuning window size.

#### b. Z-score / Standard Deviation
*   **Concept:** Measures how many standard deviations a data point is from the mean of a dataset (or a rolling window). A high absolute Z-score indicates a significant deviation.
*   **Pros:** Statistically sound, widely understood, provides a quantifiable "unusualness" score.
*   **Cons:** Assumes data is normally distributed (or close to it). Sensitive to outliers in the baseline data itself.
*   **Decision for Initial Implementation:** **Strong Candidate.** Provides a clear metric for deviation and is relatively straightforward to implement.

#### c. Exponentially Weighted Moving Average (EWMA) Control Charts
*   **Concept:** Similar to EMA, but uses control limits (typically based on multiples of the standard deviation of the EWMA) to signal out-of-control conditions.
*   **Pros:** Good for detecting small shifts in the process mean, gives more weight to recent data.
*   **Cons:** More complex than simple Z-score.

### 2. Rule-Based Systems
*   **Concept:** Define explicit rules, e.g., "If review count > X in Y hours, flag."
*   **Pros:** Very simple to implement and understand.
*   **Cons:** Not adaptable, requires manual tuning of thresholds, can generate many false positives/negatives if rules are not carefully crafted.

### 3. Machine Learning Methods (Future Consideration)

#### a. Isolation Forest
*   **Concept:** An ensemble learning method based on decision trees. It "isolates" anomalies by randomly picking a feature and then randomly picking a split value between the maximum and minimum values of the selected feature. Anomalies are points that require fewer splits to be isolated.
*   **Pros:** Effective for high-dimensional data, no need to define a distance or density measure.
*   **Cons:** Can be a black box; interpretability for analysts might be challenging. More complex to set up.

#### b. One-Class SVM (Support Vector Machine)
*   **Concept:** Learns a decision boundary that encapsulates "normal" data points. Any point outside this boundary is considered an anomaly.
*   **Pros:** Effective for complex, non-linear relationships.
*   **Cons:** Can be sensitive to hyperparameter tuning, computational cost can be high for large datasets.

## Technical Decisions & Assumptions

*   **Initial Algorithm Choice:** A **Z-score based approach** using a rolling window is selected for the initial implementation. This offers a good balance of statistical rigor, interpretability, and ease of implementation.
*   **Real-time vs. Batch:** The detection will operate on periodically aggregated velocity data (e.g., hourly), making it near real-time rather than per-review.
*   **Data Availability:** Assumed that historical review counts per product per time window will be available for baseline calculation.
*   **Configurability:** Anomaly thresholds (e.g., Z-score threshold) will be configurable.

This research will guide the implementation of the `Develop Velocity Anomaly Detection Algorithm` task.
