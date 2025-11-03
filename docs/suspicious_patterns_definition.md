# Initial Suspicious Review Patterns Definition

This document defines the initial set of suspicious review patterns for automated detection. These patterns are designed to catch common indicators of inauthentic or abusive behavior and will be used to develop the rules engine (US1.3).

## Defined Patterns (MVP)

### Rule 1: Rapid Submission Velocity

**Description:** Identifies user accounts that submit an unusually high number of reviews in a short period, especially for newly created accounts. This can be indicative of bot activity or coordinated review manipulation.

**Criteria:**
*   **User Account Age:** Less than 24 hours old.
*   **Review Count:** Submits more than 5 reviews.
*   **Time Window:** Within a 60-minute period.

**Detection Logic (Conceptual):**
1.  Fetch `userId` and `submissionTimestamp` for the new review.
2.  Check `user_creation_timestamp` for `userId`.
3.  If `user_creation_timestamp` is less than 24 hours ago:
    *   Query for all reviews by `userId` submitted within the last 60 minutes.
    *   If count > 5, flag as suspicious.

### Rule 2: Unusual Rating Deviation

**Description:** Flags reviews where the given rating significantly deviates from the product's average rating, especially for products with a substantial review history. This can indicate an attempt to unfairly boost or damage a product's reputation.

**Criteria:**
*   **Product Review Count:** Product has more than 100 existing reviews.
*   **Rating Deviation:** The review's rating is more than 2 standard deviations away from the product's current average rating.
    *   Example: A 1-star review for a product with an average rating of 4.5 and a small standard deviation.

**Detection Logic (Conceptual):**
1.  Fetch `productId` and `rating` for the new review.
2.  Query database for `average_rating` and `standard_deviation` for `productId`.
3.  If `total_reviews_count` for `productId` > 100:
    *   Calculate `z_score = (review_rating - average_rating) / standard_deviation`.
    *   If `abs(z_score)` > 2, flag as suspicious.

### Rule 3: Repetitive Phrases (Basic Keyword Matching)

**Description:** Detects reviews containing specific keywords or phrases known to be associated with spam, templated content, or low-quality/inauthentic reviews. This is a basic form and will be enhanced in future sprints.

**Criteria:**
*   **Keyword List:** A predefined list of suspicious keywords/phrases.
    *   Examples: "best product ever!!!", "super great", "must buy", "amazing quality" (when used repetitively by same user or across many low-quality reviews).
*   **Repetition:** The presence of more than one instance of a suspicious keyword/phrase in a single review, or if a specific suspicious phrase appears in multiple reviews by the same user.

**Detection Logic (Conceptual):**
1.  Fetch `text` of the new review.
2.  Iterate through a predefined list of `suspicious_keywords`.
3.  If `text` contains any `suspicious_keyword`, increment a counter.
4.  If counter > 1 (multiple keywords) OR if a keyword is found and the same user has used it in X other reviews (requires user history check), flag as suspicious.

## Future Considerations

*   Dynamic rule configuration.
*   More sophisticated natural language processing (NLP) for repetitive phrases.
*   Contextual rules based on user history, IP address, device fingerprinting.
*   Integration with external fraud detection services.
