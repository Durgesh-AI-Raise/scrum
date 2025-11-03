# Research on Common Review Abuse Patterns & Initial Categories

## 1. Introduction
This document outlines the findings from the research on common review abuse patterns and proposes an initial set of categories for the Amazon Review Integrity System (ARIS). These categories will form the foundation for configuring abuse types within the system.

## 2. Common Review Abuse Patterns Identified

Based on industry research and understanding of e-commerce fraud, the following common patterns of review abuse have been identified:

*   **Fake Reviews (Deceptive Reviews):** Reviews written by individuals who have not genuinely used or purchased the product, often for the purpose of boosting or damaging a product's reputation.
    *   **Characteristics:** Often repetitive phrasing, overly positive/negative language without specific detail, reviews posted in batches, reviewers with no purchase history for the product.
*   **Incentivized Reviews:** Reviews solicited or paid for, where the reviewer receives a benefit (e.g., free product, discount, monetary compensation) in exchange for a positive review. Amazon's policy prohibits incentivized reviews where the incentive is conditioned on the review being positive or where the seller manipulates review placement.
    *   **Characteristics:** Disclosure of incentive (sometimes subtle), sudden spikes in reviews after product launch, reviewers often part of known "review clubs".
*   **Competitor Sabotage (Negative Review Campaigns):** Coordinated efforts by competitors to post numerous negative reviews to damage a product's or seller's reputation.
    *   **Characteristics:** Unusually high volume of 1-star reviews in a short period, often lacking specific details, similar phrasing across multiple negative reviews, reviewers with no history of buying from the targeted seller.
*   **Reviewer Account Compromise:** Reviews posted from hijacked legitimate accounts.
    *   **Characteristics:** Reviews inconsistent with historical reviewer behavior, reviews for products not typically purchased by the account owner, sudden surge in review activity from an otherwise dormant account.
*   **Self-Promotion/Seller Reviews:** Sellers posting reviews for their own products or asking employees/family members to do so.
    *   **Characteristics:** Highly promotional language, often from new accounts or accounts with strong ties to the seller.
*   **Duplicate Reviews/Spam:** Identical or near-identical reviews posted across multiple products, sellers, or by multiple accounts.
    *   **Characteristics:** Repetitive text, generic content.

## 3. Proposed Initial Abuse Type Categories for ARIS

Based on the patterns identified, we propose the following initial high-level categories for the ARIS system:

1.  **Fake Reviews**
    *   **Description:** Reviews created with malicious intent to manipulate product perception, not reflecting a genuine customer experience. This includes both artificially positive and negative (non-competitor sabotage) reviews.
    *   **Severity:** HIGH

2.  **Incentivized Reviews**
    *   **Description:** Reviews provided in exchange for compensation or free products, violating Amazon's policies on unbiased reviews.
    *   **Severity:** MEDIUM to HIGH (depending on the nature of the incentive and impact)

3.  **Competitor Sabotage**
    *   **Description:** Coordinated campaigns by competitors to artificially lower a product's rating or reputation through fraudulent negative reviews.
    *   **Severity:** HIGH

4.  **Account Compromise**
    *   **Description:** Reviews posted from reviewer accounts that have been illicitly accessed and used by malicious actors.
    *   **Severity:** HIGH

5.  **Spam/Duplicate Content**
    *   **Description:** Reviews containing generic, repeated, or irrelevant content, often posted in bulk to inflate review counts or spread misinformation.
    *   **Severity:** LOW to MEDIUM

This initial categorization provides a framework for the data model and subsequent detection logic development. Further refinement and addition of sub-categories may occur as the system evolves.
