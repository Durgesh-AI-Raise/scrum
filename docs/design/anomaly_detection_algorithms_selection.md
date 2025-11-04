# Anomaly Detection Algorithms Selection for Review Integrity System

## User Story: As a Review Integrity System, I need to detect anomalous review patterns... (Issue #10454)

This document outlines the research and selection of anomaly detection algorithms for the initial implementation of the Review Integrity System, focusing on review velocity spikes and unusual rating distributions.

### 1. Requirements & Goals

*   **Review Velocity:** Detect sudden, significant increases in review volume for a product or seller within a defined time window. This indicates potential "review bombing" or coordinated false reviews.
*   **Rating Distribution:** Identify skewed or unusual patterns in star rating distributions (e.g., an overwhelming number of 5-star or 1-star reviews compared to historical norms or a balanced distribution). This could indicate review manipulation.
*   **Constraints:** Solutions should be computationally efficient, scalable, and provide reasonable interpretability for initial flagging.

### 2. Candidate Algorithms Explored

#### 2.1 For Review Velocity (Time-Series Anomaly Detection)

*   **Statistical Methods:**
    *   **Z-score (Standard Score):** Measures how many standard deviations an observation is from the mean. Simple, effective for sudden deviations.
    *   **EWMA (Exponentially Weighted Moving Average):** Gives more weight to recent observations, making it more responsive to recent changes while still smoothing out noise.
*   **Machine Learning Methods:**
    *   **Isolation Forest:** An ensemble method that "isolates" anomalies by randomly selecting a feature and then randomly selecting a split value between the maximum and minimum values of the selected feature.
    *   **One-Class SVM:** Learns a decision boundary for normal data points and flags points outside this boundary as anomalies.
    *   **Prophet (Facebook):** A forecasting tool that can also detect anomalies by flagging points outside prediction intervals.

#### 2.2 For Rating Distribution (Distributional Anomaly Detection)

*   **Statistical Methods:**
    *   **Chi-squared Test:** Compares an observed frequency distribution (e.g., current rating counts) with an expected frequency distribution (e.g., historical average or uniform distribution) to see if there's a statistically significant difference.
    *   **Kullback-Leibler (KL) Divergence / Jensen-Shannon Divergence:** Measures the statistical distance between two probability distributions. Useful for quantifying how much one distribution differs from another.
*   **Clustering Methods:**
    *   **DBSCAN/K-Means:** Could be used to cluster "normal" rating distributions and identify outliers that don't fit into any cluster. (More complex for initial MVP).

### 3. Algorithm Selection for MVP

Based on the requirements for computational efficiency, interpretability, and ease of initial implementation, the following algorithms are selected for the Minimum Viable Product (MVP):

*   **Review Velocity Spikes: Z-score**
    *   **Reasoning:** Straightforward to implement, highly interpretable (how many standard deviations away from the norm), and computationally inexpensive for real-time monitoring. It effectively flags sudden, significant deviations from a rolling average.
    *   **Future Consideration:** EWMA or Isolation Forest could be explored later for more nuanced pattern detection or to handle seasonality if Z-score proves insufficient.

*   **Unusual Rating Distributions: Chi-squared Test**
    *   **Reasoning:** A well-established statistical test for comparing observed and expected categorical distributions. It provides a clear statistical measure of whether the current rating distribution significantly deviates from a known baseline (e.g., historical average distribution for the product/seller, or a general balanced distribution).
    *   **Future Consideration:** KL Divergence could offer a more continuous measure of distribution difference and may be considered for refining the scoring mechanism.

### 4. High-Level Implementation Strategy

*   **Data Ingestion:** Ensure robust pipelines for aggregating review counts over time intervals and capturing star rating counts per product/seller.
*   **Baselining:** Establish historical means and standard deviations (for Z-score) or expected distributions (for Chi-squared) for comparison. This will likely involve a warm-up period or historical data analysis.
*   **Thresholding:** Define appropriate Z-score thresholds and Chi-squared significance levels (p-values) to balance false positives and false negatives. These will likely be tunable parameters.
*   **Flagging:** The output of these detection modules will feed into a central flagging mechanism, generating alerts or contributing to a review's overall risk score.
