# Review Abuse Detection Rules

## Sprint 1: Identical Review Text Detection

### Rule ID: `IDENTICAL_REVIEW_TEXT_001`

**Description:** This rule identifies reviews that have an exact match in their `text` content. This is a foundational rule to detect obvious patterns of review manipulation, such as copy-pasting reviews across different products or by different reviewers.

**Criteria:**
*   **Match Type:** Exact string match.
*   **Field(s) for Comparison:** `review.text`
*   **Case Sensitivity:** Yes (case-sensitive match).
*   **Scope:** All reviews processed within the current ingestion batch. Future iterations may expand this to compare against a historical window of reviews or specific product/reviewer contexts.

**Technical Considerations/Assumptions:**
*   Initial implementation will not perform text normalization (e.g., removing punctuation, converting to lowercase, handling whitespace variations). This is a planned enhancement for future sprints.
*   The detection module will group reviews by identical text and flag all but the first occurrence (or all occurrences as part of an incident).
*   This rule is a basic heuristic and may result in false positives or false negatives, which will be refined with more advanced techniques later.

**Example Scenario:**
*   Review A: "This product is amazing, I highly recommend it!"
*   Review B: "This product is amazing, I highly recommend it!"
*   Review C: "This product is amazing, I highly recommend it!"

Reviews A, B, and C would be flagged as identical based on this rule.
