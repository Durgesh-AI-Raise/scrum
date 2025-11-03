
# Rule Engine Design

## Overview
The Rule Engine is a core component of ARIS, responsible for automatically evaluating incoming reviews against a set of predefined rules to identify suspicious activity. It is designed to be extensible, allowing for new rule types to be added with minimal changes to the core engine.

## Core Components

### 1. `Rule` Base Class
An abstract base class for all rules. It defines common attributes like `id`, `name`, `type`, `definition` (JSON payload specific to the rule type), `severity`, and `isEnabled`. It also declares an abstract `evaluate` method that concrete rule implementations must override.

### 2. Concrete Rule Classes
Subclasses of `Rule` that implement specific flagging logic. Examples include:
- `IpMatchRule`: Checks if the reviewer's IP address matches a list of known suspicious IPs.
- `KeywordMatchRule`: Scans review text for specific keywords or phrases.
- `RapidReviewRule` (Placeholder): Intended for detecting rapid review patterns (e.g., many reviews from one user in a short period). This will initially be a placeholder and require external service integration for full functionality.

### 3. `RuleEngine` Class
The orchestrator of rule evaluation.
- **`__init__()`**: Initializes the engine, potentially loading rules from a persistent store.
- **`load_rules()`**: Fetches active rules from the database and instantiates their respective `Rule` objects, storing them in an internal cache.
- **`evaluate_review(review_data)`**: Takes an incoming `ReviewData` object, iterates through active rules, and calls each rule's `evaluate` method. It aggregates all triggered flags.

### 4. `ReviewData` Model
A simple data transfer object (DTO) to encapsulate relevant review information passed to the rule engine for evaluation.

## Data Flow
1. An incoming review is processed by the `FlaggingService`.
2. The `FlaggingService` converts the raw review into a `ReviewData` object.
3. The `ReviewData` object is passed to `RuleEngine.evaluate_review()`.
4. The `RuleEngine` iterates through its loaded `Rule` objects.
5. Each active `Rule`'s `evaluate()` method is called with the `ReviewData`.
6. If a rule evaluates to `True` (i.e., it flags the review), details of the triggered rule are collected.
7. The `RuleEngine` returns a list of triggered flags to the `FlaggingService`.

## Rule Definition Structure (JSON examples for `definition` field)

*   **IP Match:**
    ```json
    {"ips": ["192.168.1.1", "10.0.0.5"]}
    ```
*   **Keyword Match (Any):**
    ```json
    {"keywords": ["scam", "fake", "fraud"], "match_any": true}
    ```
*   **Keyword Match (All):**
    ```json
    {"keywords": ["fake", "review"], "match_any": false}
    ```
*   **Rapid Review (Placeholder):**
    ```json
    {"max_reviews": 5, "time_window_minutes": 60, "group_by": "product_id"}
    ```
    (Note: Actual implementation will involve querying a review history service.)

## Scalability Considerations
- **Rule Caching:** Rules are loaded into memory to minimize database lookups during high-volume review processing.
- **Asynchronous Processing:** The `FlaggingService` (which uses the Rule Engine) could process reviews asynchronously (e.g., via a message queue) to decouple review ingestion from flagging.
- **Rule Management API:** A dedicated API (User Story 6) will allow dynamic updates to rules without redeploying the core engine.
