# Amazon Review Data Sources Research Findings

## Objective
To identify the most suitable method for real-time ingestion of Amazon product reviews, considering scalability, reliability, and compliance.

## Findings

### 1. Amazon Product Advertising API (PA-API)
*   **Overview:** Primarily designed for affiliates to advertise products.
*   **Review Data:** Generally provides aggregated review information (e.g., average rating, number of reviews) and often links to reviews on Amazon.com, but *not* the full review text content directly for mass consumption.
*   **Real-time suitability:** Low for full review content.
*   **Compliance:** High, but limited utility for our specific need.

### 2. Amazon MWS / Seller Central / Vendor Central APIs
*   **Overview:** Designed for sellers and vendors to manage their own products, orders, and listings.
*   **Review Data:** Provides access to reviews *only for products sold by the account holder*. Does not provide a broad spectrum of reviews across Amazon.
*   **Real-time suitability:** Moderate for specific use cases (own products).
*   **Compliance:** High, but scope-limited.

### 3. Third-Party Data Providers / APIs
*   **Overview:** Several companies specialize in collecting and providing Amazon product data, including reviews. They handle the complexities of data acquisition (often through a mix of legitimate APIs and sophisticated scraping) and offer structured feeds.
*   **Examples:** DataForSEO, ScrapeHero, Oxylabs (for data collection infrastructure).
*   **Review Data:** Can provide full review content, metadata, and offer real-time or near real-time updates.
*   **Real-time suitability:** High.
*   **Compliance:** Varies by provider; requires due diligence on their methods and terms. Often comes with a cost.

### 4. Web Scraping
*   **Overview:** Directly parsing review pages on Amazon.com.
*   **Review Data:** Can potentially capture all visible review data.
*   **Real-time suitability:** Can be high, but technically challenging to maintain due to website changes, CAPTCHAs, and IP blocking.
*   **Compliance:** Very Low. Violates Amazon's Terms of Service (Section 7 - License and Access: "You may not extract and/or re-utilize parts of the content of any Amazon Service without our express written consent."). Significant legal risks.
*   **Recommendation:** Avoid for production systems unless explicitly sanctioned and managed with extreme care.

## Recommendation for Sprint 1 (MVP)

Given the "real-time" and "all new reviews" requirements, a **specialized third-party data provider** is the most viable and compliant option for broad Amazon review ingestion. For the immediate implementation phase, we will assume an API endpoint from such a provider that delivers new reviews as they are posted. If budget or approval for a third-party service is pending, we will develop against a **simulated stream** to unblock development, with a clear understanding that the integration point will need to be swapped later.

**Decision for Development:** Proceed with the design assuming a reliable `review_api.get_new_reviews()` or a callback/webhook mechanism from a source that provides structured review data.
