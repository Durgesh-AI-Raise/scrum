# Documentation for Task 2.1: Selected ML Algorithms

## Anomalous Review Pattern Detection Model

### 1. Types of Anomalies Targeted:
*   **Unusual phrasing/Generic language:** Reviews that deviate significantly from typical language patterns for a given product or overall corpus.
*   **Duplicate/Near-duplicate content:** Reviews that are identical or highly similar to others.
*   **Sudden spikes in review volume:** An unusually high number of reviews submitted within a short timeframe.
*   **Outlier review metadata:** Reviews with unusual ratings, timestamps, or device/IP information compared to the norm.

### 2. Selected Baseline ML Algorithms:

#### a) For Text-based Anomalies (Unusual Phrasing, Generic Language, Duplicates):
*   **Isolation Forest:**
    *   **Rationale:** Effective for high-dimensional data, performs well on isolating outliers by randomly selecting features and splitting values. Anomalies are data points that are "isolated" more easily. It's unsupervised, which is suitable given potentially limited labeled anomaly data.
    *   **Features considered:** TF-IDF vectors of `review_text`, potentially combined with other numerical features derived from text (e.g., text length, sentiment scores).
*   **TF-IDF + Cosine Similarity:**
    *   **Rationale:** Directly identifies near-duplicate reviews by computing the cosine similarity between TF-IDF vectors of review texts. A very high similarity score (e.g., >0.95) indicates a near-duplicate. Can also be used to identify generic language by comparing against a centroid of "normal" reviews.
    *   **Features considered:** `review_text`.

#### b) For Volume-based Anomalies (Sudden Spikes):
*   **Statistical Thresholding (e.g., Z-score or Rolling Standard Deviation):**
    *   **Rationale:** A straightforward and computationally inexpensive method to detect deviations from expected review rates. By monitoring the count of reviews per time window (e.g., per hour), a sudden increase that significantly exceeds a defined statistical threshold (e.g., 3 standard deviations above the rolling mean) can be flagged.
    *   **Features considered:** Count of reviews per time unit (e.g., `timestamp`).

#### c) For Outlier Review Metadata (Initial consideration, to be integrated with Isolation Forest):
*   **Isolation Forest:**
    *   **Rationale:** Can also incorporate numerical metadata features (e.g., `rating`, derived features from `device_info` or `ip_address` if suitable numerical representations are created) to detect multivariate outliers.

### 3. Future Considerations/Enhancements:
*   **One-Class SVM:** As an alternative for unsupervised anomaly detection on structured/textual features.
*   **Autoencoders:** For learning more complex representations of "normal" review text and detecting anomalies based on high reconstruction error.
*   **Sentiment Analysis:** Integrate sentiment scores as a feature, and flag reviews where sentiment drastically differs from the product's overall sentiment or common review sentiment for a given rating.
*   **Word Embeddings (Word2Vec, BERT):** For more nuanced understanding of review text and detecting semantic anomalies, particularly for unusual phrasing.
