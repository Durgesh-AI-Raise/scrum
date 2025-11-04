# Initial Detection Algorithms/Models Research Summary

For the initial sprint, the focus will be on implementing rule-based detection algorithms due to their simplicity and ease of implementation. These can serve as a strong baseline before exploring more complex machine learning models.

## Selected Algorithms/Patterns:

1.  **Review Velocity Check:**
    *   **Description:** Flags reviewers who post an abnormally high number of reviews within a short timeframe. This can indicate coordinated abuse or bot activity.
    *   **Rule Example:** Flag if a reviewer has submitted more than `X` reviews in the last `Y` days.
    *   **Initial Thresholds (to be refined):** More than 10 reviews in 7 days.

2.  **Keyword Stuffing Detection:**
    *   **Description:** Identifies reviews containing an unusually high density of specific keywords, often promotional or overly positive/negative, suggesting automated generation or deceptive intent.
    *   **Rule Example:** Flag if the percentage of "suspicious" keywords (e.g., "amazing", "best", "love", "must-buy") exceeds `Z%` of the total words in the review text.
    *   **Initial Thresholds (to be refined):** > 30% of words are from a predefined list of suspicious keywords.

3.  **New Account High Volume Detection:**
    *   **Description:** Targets newly created accounts that immediately post a large number of reviews, which is a common pattern for "sockpuppet" accounts or new botnets.
    *   **Rule Example:** Flag if the reviewer's account age is less than `N` days AND they have submitted more than `M` reviews in total.
    *   **Initial Thresholds (to be refined):** Account created less than 30 days ago AND total reviews by account > 5.

## Future Considerations:

*   Sentiment analysis integration.
*   Geolocation consistency checks.
*   Review content similarity (detecting copied reviews).
*   Anomaly detection using machine learning models (e.g., isolation forests, autoencoders) for more sophisticated patterns.
*   User behavior analytics (e.g., browsing patterns, purchase history correlations).
