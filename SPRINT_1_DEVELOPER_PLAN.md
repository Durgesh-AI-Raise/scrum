# Sprint 1 Developer Plan: Amazon Review Integrity Guardian (RIG)

---

### 1) Overall Architecture Vision

For the Amazon Review Integrity Guardian (RIG) system, a serverless, event-driven architecture on AWS is chosen for its scalability, real-time processing capabilities, and cost-effectiveness.

*   **Data Ingestion:** AWS Kinesis Data Streams will handle near real-time ingestion. Kinesis Firehose will then deliver raw data to Amazon S3 for durable storage (data lake). AWS Lambda functions will process data from either Kinesis or S3.
*   **Data Storage:** Amazon S3 will serve as the raw data lake. Amazon DynamoDB will store processed review data, metadata, and flagged statuses, offering low-latency access and high scalability.
*   **Abuse Detection:** AWS Lambda functions, triggered by DynamoDB Streams or S3 events, will implement the rule-based detection logic.
*   **Dashboard & Manual Flagging:** Amazon API Gateway will expose RESTful APIs, backed by AWS Lambda functions. The frontend dashboard will be a single-page application hosted on Amazon S3, potentially accelerated by Amazon CloudFront.
*   **Security:** AWS IAM roles, KMS encryption, and VPC endpoints will secure data in transit and at rest, and control access to resources.

---

### 2) Data Models and Architecture Definition

#### Data Model: `Reviews` (DynamoDB Table)

This will be the central table for all review data, including their status and flagging information.

*   **Primary Key:** `reviewId` (String)
*   **Attributes:**
    *   `reviewId`: String (e.g., "R1A2B3C4D5E6")
    *   `reviewerId`: String (e.g., "A1B2C3D4E5F6")
    *   `productId`: String (e.g., "B0000DGF0G")
    *   `reviewText`: String (The full review text)
    *   `rating`: Number (1-5 stars)
    *   `timestamp`: Number (Unix epoch milliseconds of review creation)
    *   `purchaseVerified`: Boolean (True if review is from a verified purchase)
    *   `ingestionTimestamp`: Number (Unix epoch milliseconds of ingestion)
    *   `status`: String ("INGESTED", "FLAGGED", "ABUSIVE")
    *   `abuseReason`: String (Optional - auto-detected reason, e.g., "Duplicate text across products")
    *   `flaggedTimestamp`: Number (Optional - Unix epoch milliseconds when system flagged)
    *   `manualAbuseReason`: String (Optional - analyst-provided reason for manual flagging)
    *   `abusedByAnalystId`: String (Optional - ID of the analyst who manually marked as abusive)
    *   `manualFlaggingTimestamp`: Number (Optional - Unix epoch milliseconds when analyst flagged)

*   **Global Secondary Index (GSI):** `StatusIndex` on `status` attribute, enabling efficient querying for flagged reviews.

#### Data Model: `ReviewTextHashes` (DynamoDB Table)

This auxiliary table will store hashes of review texts to quickly identify duplicates across products.

*   **Primary Key:** `reviewTextHash` (String)
*   **Attributes:**
    *   `reviewTextHash`: String (SHA256 hash of `reviewText`)
    *   `productIds`: Set<String> (Set of product IDs associated with this `reviewTextHash`)
    *   `reviewIds`: Set<String> (Set of review IDs associated with this `reviewTextHash`)
    *   `firstSeenTimestamp`: Number (Unix epoch milliseconds when this hash was first encountered)
    *   `lastSeenTimestamp`: Number (Unix epoch milliseconds when this hash was last encountered)
    *   `count`: Number (Total count of reviews with this hash)

---

### 3) Implementation Plan by User Story and Task

#### User Story 1: Secure Data Ingestion (60 hours)

*   **Task 1.1: Design data ingestion pipeline covering source, format, frequency, and security considerations.**
    *   **Implementation Plan:** Define the pipeline using AWS Kinesis Data Streams as the entry point. Data will be assumed to be pushed in JSON format. Near real-time processing (seconds latency) is the target frequency. Security will be enforced using IAM roles for Kinesis producers and consumers, KMS for encryption at rest (S3, DynamoDB), and Network ACLs/Security Groups for VPC connectivity if applicable.
    *   **Assumptions:** Amazon review data is available as a streamable source, and we can configure a mechanism (e.g., Kinesis Producer Library, direct API calls) to push it into our Kinesis stream. Data will be in a structured JSON format.
    *   **Technical Decisions:** AWS Kinesis Data Stream for real-time ingestion, AWS Kinesis Firehose for S3 delivery, AWS S3 for raw data storage.

*   **Task 1.2: Implement the necessary data connectors to pull data from Amazon review data streams.**
    *   **Implementation Plan:** As data is assumed to be pushed into Kinesis, this task focuses on setting up the Kinesis Data Stream itself and configuring its integration with downstream services. No active "pull" mechanism from an external Amazon review stream is explicitly developed in this sprint, rather the Kinesis Stream acts as the "connector endpoint".
    *   **Technical Decisions:** Configure an AWS Kinesis Data Stream.

*   **Task 1.3: Set up secure storage solutions (e.g., S3 bucket, data lake) for the raw ingested review data.**
    *   **Implementation Plan:** Create a dedicated S3 bucket ('''rig-raw-review-data-lake-prod'''). Configure Kinesis Firehose to stream data from the Kinesis Data Stream to this S3 bucket. Implement S3 bucket policies to restrict access using IAM roles and enable default encryption (SSE-S3 or SSE-KMS).
    *   **Technical Decisions:** S3 for raw data lake, Kinesis Firehose for automated delivery, S3 bucket policies and encryption.

*   **Task 1.4: Develop routines to validate and cleanse the ingested review data to ensure quality.**
    *   **Implementation Plan:** An AWS Lambda function ('''IngestionValidatorLambda''') will be triggered by Kinesis Data Stream events (or Firehose transformation). This Lambda will perform schema validation (e.g., check for mandatory fields like '''reviewId''', '''productId''', '''reviewText'''), data type validation (e.g., '''rating''' is a number), and basic cleansing (e.g., trimming whitespace from strings, handling nulls gracefully). Validated data will then be written to the `Reviews` DynamoDB table. Invalid records will be logged to CloudWatch and potentially sent to a Dead-Letter Queue (DLQ).
    *   **Code Snippet (Pseudocode for `IngestionValidatorLambda`):**
        ```python
        import json
        import base64
        import time

        def ingestion_validator_lambda(event, context):
            processed_records = []
            for record in event['Records']:
                try:
                    # Kinesis Stream record structure
                    payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
                    review = json.loads(payload)

                    # Add ingestion timestamp and initial status
                    review['ingestionTimestamp'] = int(time.time() * 1000)
                    review['status'] = 'INGESTED'

                    # --- Validation Logic ---
                    # Check for mandatory fields
                    if not all(key in review for key in ['reviewId', 'productId', 'reviewText', 'rating', 'timestamp', 'reviewerId', 'purchaseVerified']):
                        print(f"Validation failed: Missing mandatory fields for review: {review.get('reviewId')}")
                        continue

                    # Validate data types
                    if not isinstance(review['rating'], int) or not (1 <= review['rating'] <= 5):
                        print(f"Validation failed: Invalid rating for review: {review.get('reviewId')}")
                        continue
                    if not isinstance(review['timestamp'], int):
                        print(f"Validation failed: Invalid timestamp for review: {review.get('reviewId')}")
                        continue
                    
                    # Basic cleansing (e.g., trim strings)
                    review['reviewText'] = review['reviewText'].strip()
                    review['reviewerId'] = review['reviewerId'].strip()
                    review['productId'] = review['productId'].strip()

                    # --- Store in DynamoDB ---
                    # dynamodb_table.put_item(Item=review)
                    print(f"Successfully validated and prepared review {review.get('reviewId')} for storage.")
                    processed_records.append(review)

                except Exception as e:
                    print(f"Error processing record: {e}. Record: {record}")
                    # Optionally send to a DLQ for further investigation
            
            # For demonstration, returning processed records. In real-world, this would interact with DynamoDB
            return {'statusCode': 200, 'body': json.dumps({'message': f'Processed {len(processed_records)} records.'})}
        ```

*   **Task 1.5: Implement a mechanism for near real-time processing of newly ingested review data.**
    *   **Implementation Plan:** This is achieved by configuring the `IngestionValidatorLambda` (from Task 1.4) to directly consume from the Kinesis Data Stream. Kinesis provides native integration with Lambda, allowing it to process records as soon as they become available in the stream, ensuring near real-time data flow into DynamoDB.
    *   **Technical Decisions:** Kinesis Data Stream as a Lambda event source.

#### User Story 2 (Partial): Initial Rule-Based Detection (28 hours)

*   **Task 2.1: Research and document an initial set of common review abuse patterns (e.g., duplicate text).**
    *   **Implementation Plan:** For this sprint, the primary focus is on detecting **identical review text across different products**. This pattern indicates potential spamming or organized abuse.
    *   **Assumptions:** Exact string matching is sufficient for initial detection. More advanced semantic similarity will be deferred.

*   **Task 2.2: Develop a rule engine to detect instances of identical review text across different products.**
    *   **Implementation Plan:** An AWS Lambda function ('''DuplicateTextDetectorLambda''') will be triggered by DynamoDB Streams whenever a new item is inserted into the `Reviews` table. This Lambda will:
        1.  Calculate a SHA256 hash of the `reviewText`.
        2.  Query the `ReviewTextHashes` DynamoDB table using this hash.
        3.  If the hash exists:
            *   Check if the `productId` associated with the current review is already in the `productIds` set for that hash.
            *   If the `productId` is *new* to that hash, it indicates a duplicate review text across different products.
            *   Update the `ReviewTextHashes` entry to include the new `productId` and `reviewId`.
        4.  If the hash does not exist:
            *   Create a new entry in `ReviewTextHashes` with the hash, current `productId`, `reviewId`, and timestamps.
    *   **Technical Decisions:** DynamoDB Streams as a Lambda event source. Use a separate DynamoDB table (`ReviewTextHashes`) for efficient hash lookups.
    *   **Code Snippet (Pseudocode for `DuplicateTextDetectorLambda`):**
        ```python
        import json
        import hashlib
        import time

        def duplicate_text_detector_lambda(event, context):
            for record in event['Records']:
                if record['eventName'] == 'INSERT':  # Process only newly inserted reviews
                    new_image = record['dynamodb']['NewImage']
                    review_id = new_image['reviewId']['S']
                    product_id = new_image['productId']['S']
                    review_text = new_image['reviewText']['S']

                    review_text_hash = hashlib.sha256(review_text.encode('utf-8')).hexdigest()
                    current_timestamp = int(time.time() * 1000)

                    # --- DynamoDB interaction pseudocode for ReviewTextHashes table ---
                    # Check if hash exists
                    # response = dynamodb_client.get_item(
                    #     TableName='ReviewTextHashes',
                    #     Key={'reviewTextHash': {'S': review_text_hash}}
                    # )
                    # existing_item = response.get('Item')

                    existing_item = None # Placeholder for actual DB lookup

                    if existing_item:
                        # Convert DynamoDB 'Set' type to Python set
                        existing_product_ids = set(existing_item['productIds']['SS'])
                        existing_review_ids = set(existing_item['reviewIds']['SS'])

                        # If this review's product ID is new for this review text hash
                        if product_id not in existing_product_ids:
                            # Flag this review as abusive (Task 2.4)
                            # flag_review_as_abusive(review_id, "Duplicate text across products")
                            print(f"FLAGGED: Review {review_id} (product {product_id}) has duplicate text across products.")

                        # Update existing entry with new product/review IDs and timestamps
                        existing_product_ids.add(product_id)
                        existing_review_ids.add(review_id)
                        
                        # dynamodb_client.update_item(
                        #     TableName='ReviewTextHashes',
                        #     Key={'reviewTextHash': {'S': review_text_hash}},
                        #     UpdateExpression="SET productIds = :pids, reviewIds = :rids, lastSeenTimestamp = :lst, #c = #c + :inc",
                        #     ExpressionAttributeNames={'#c': 'count'},
                        #     ExpressionAttributeValues={
                        #         ':pids': {'SS': list(existing_product_ids)},
                        #         ':rids': {'SS': list(existing_review_ids)},
                        #         ':lst': {'N': str(current_timestamp)},
                        #         ':inc': {'N': '1'}
                        #     }
                        # )
                    else:
                        # Create new entry
                        # dynamodb_client.put_item(
                        #     TableName='ReviewTextHashes',
                        #     Item={
                        #         'reviewTextHash': {'S': review_text_hash},
                        #         'productIds': {'SS': [product_id]},
                        #         'reviewIds': {'SS': [review_id]},
                        #         'firstSeenTimestamp': {'N': str(current_timestamp)},
                        #         'lastSeenTimestamp': {'N': str(current_timestamp)},
                        #         'count': {'N': '1'}
                        #     }
                        # )
                        print(f"New review text hash recorded for review {review_id}.")

        # Helper function (pseudocode) for flagging a review
        def flag_review_as_abusive(review_id, reason):
            # dynamodb_client.update_item(
            #     TableName='Reviews',
            #     Key={'reviewId': {'S': review_id}},
            #     UpdateExpression="SET #s = :s, abuseReason = :ar, flaggedTimestamp = :ft",
            #     ExpressionAttributeNames={'#s': 'status'},
            #     ExpressionAttributeValues={
            #         ':s': {'S': 'FLAGGED'},
            #         ':ar': {'S': reason},
            #         ':ft': {'N': str(int(time.time() * 1000))}
            #     }
            # )
            print(f"Review {review_id} flagged with reason: {reason}")
        ```

*   **Task 2.4: Implement a mechanism to flag reviews identified by the rule engines as potentially abusive.**
    *   **Implementation Plan:** The `DuplicateTextDetectorLambda` (from Task 2.2) will be responsible for updating the `Reviews` DynamoDB table. When a review is identified as potentially abusive (e.g., duplicate text across products), its `status` field will be updated from "INGESTED" to "FLAGGED", and the `abuseReason` and `flaggedTimestamp` fields will be populated.
    *   **Technical Decisions:** Direct update to the `Reviews` DynamoDB table via the Lambda function.

#### User Story 3 (Partial): Basic Flagged Reviews Dashboard (36 hours)

*   **Task 3.1: Design the layout and specify required data elements for a basic dashboard displaying flagged reviews.**
    *   **Implementation Plan:** The dashboard will display a tabular list of flagged reviews. Each row will include: `reviewId`, `productId`, `reviewText` (truncated for brevity), `abuseReason`, `flaggedTimestamp` (formatted), `reviewerId`. Each row will also feature action buttons: "View Details" (placeholder for future functionality) and "Mark as Abusive" (for User Story 4).
    *   **Required Data Elements:** `reviewId`, `productId`, `reviewText`, `abuseReason`, `flaggedTimestamp`, `reviewerId`.

*   **Task 3.2: Develop the necessary backend API to fetch flagged review data for display on the dashboard.**
    *   **Implementation Plan:** Create an AWS API Gateway REST API endpoint (e.g., `GET /flagged-reviews`). This endpoint will trigger an AWS Lambda function ('''GetFlaggedReviewsLambda'''). This Lambda will query the `Reviews` DynamoDB table using the `StatusIndex` to retrieve all items where `status` is "FLAGGED". The results will be paginated and returned as JSON.
    *   **Technical Decisions:** API Gateway for external access, Lambda for backend logic, DynamoDB with a GSI for efficient querying.
    *   **Code Snippet (Pseudocode for `GetFlaggedReviewsLambda`):**
        ```python
        import json
        # import boto3 # For actual DynamoDB client

        # dynamodb = boto3.resource('dynamodb')
        # reviews_table = dynamodb.Table('Reviews')

        def get_flagged_reviews_lambda(event, context):
            try:
                # Query DynamoDB for items with status 'FLAGGED'
                # response = reviews_table.query(
                #     IndexName='StatusIndex',
                #     KeyConditionExpression='#s = :status_val',
                #     ExpressionAttributeNames={
                #         '#s': 'status'
                #     },
                #     ExpressionAttributeValues={
                #         ':status_val': 'FLAGGED'
                #     }
                # )
                # flagged_reviews = response.get('Items', [])

                # Placeholder for actual data fetch
                flagged_reviews = [
                    {
                        "reviewId": "rev123-dup",
                        "reviewerId": "userXYZ",
                        "productId": "prodABC",
                        "reviewText": "This review text is identical across different products, clearly spam.",
                        "rating": 1,
                        "timestamp": 1678886000000,
                        "purchaseVerified": True,
                        "ingestionTimestamp": 1678886100000,
                        "status": "FLAGGED",
                        "abuseReason": "Duplicate text across products",
                        "flaggedTimestamp": 1678886200000
                    },
                    {
                        "reviewId": "rev456-dup",
                        "reviewerId": "userPQR",
                        "productId": "prodDEF",
                        "reviewText": "Another dummy review text that is duplicated.",
                        "rating": 1,
                        "timestamp": 1678886500000,
                        "purchaseVerified": False,
                        "ingestionTimestamp": 1678886600000,
                        "status": "FLAGGED",
                        "abuseReason": "Duplicate text across products",
                        "flaggedTimestamp": 1678886700000
                    }
                ]

                # Convert DynamoDB items to standard JSON format if needed (e.g., remove type descriptors like {'S': 'value'})
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*' # Required for CORS from frontend
                    },
                    'body': json.dumps(flagged_reviews)
                }
            except Exception as e:
                print(f"Error fetching flagged reviews: {e}")
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'message': 'Failed to retrieve flagged reviews.'})
                }
        ```

*   **Task 3.3: Implement the front-end user interface component responsible for rendering the flagged reviews on the dashboard.**
    *   **Implementation Plan:** Develop a single-page application (SPA) using a modern JavaScript framework (e.g., React, Vue). This SPA will make an AJAX call to the `GET /flagged-reviews` API Gateway endpoint, fetch the data, and render it in an HTML table. The application will be hosted on S3 and accessible via a static website endpoint.
    *   **Technical Decisions:** React (or similar) for frontend, S3 for static website hosting.
    *   **Code Snippet (Pseudocode for `FlaggedReviewsDashboard.js` React Component):**
        ```javascript
        import React, { useState, useEffect } from 'react';

        const API_ENDPOINT = 'YOUR_API_GATEWAY_ENDPOINT'; // Replace with actual API Gateway URL

        function FlaggedReviewsDashboard() {
            const [reviews, setReviews] = useState([]);
            const [loading, setLoading] = useState(true);
            const [error, setError] = useState(null);

            const fetchFlaggedReviews = async () => {
                try {
                    setLoading(true);
                    const response = await fetch(`${API_ENDPOINT}/flagged-reviews`);
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const data = await response.json();
                    setReviews(data);
                } catch (err) {
                    setError(err);
                } finally {
                    setLoading(false);
                }
            };

            useEffect(() => {
                fetchFlaggedReviews();
            }, []); // Empty dependency array means this runs once on mount

            const handleMarkAsAbusive = async (reviewId) => {
                const reason = prompt("Enter reason for marking as abusive:");
                if (!reason) return;

                try {
                    const response = await fetch(`${API_ENDPOINT}/reviews/${reviewId}/status`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            status: 'ABUSIVE',
                            reason: reason,
                            analystId: 'AmazonAnalyst1' // Placeholder for actual authenticated user
                        }),
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    alert(`Review ${reviewId} marked as abusive.`);
                    fetchFlaggedReviews(); // Refresh the list
                } catch (err) {
                    console.error('Error marking review as abusive:', err);
                    alert('Failed to mark review as abusive.');
                }
            };

            if (loading) return <p>Loading flagged reviews...</p>;
            if (error) return <p>Error: {error.message}</p>;

            return (
                <div style={{ padding: '20px' }}>
                    <h1>Amazon Review Integrity Guardian Dashboard</h1>
                    <h2>Flagged Reviews</h2>
                    {reviews.length === 0 ? (
                        <p>No flagged reviews found.</p>
                    ) : (
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ borderBottom: '1px solid #ccc' }}>
                                    <th style={{ padding: '8px', textAlign: 'left' }}>Review ID</th>
                                    <th style={{ padding: '8px', textAlign: 'left' }}>Product ID</th>
                                    <th style={{ padding: '8px', textAlign: 'left' }}>Review Text</th>
                                    <th style={{ padding: '8px', textAlign: 'left' }}>Abuse Reason</th>
                                    <th style={{ padding: '8px', textAlign: 'left' }}>Flagged At</th>
                                    <th style={{ padding: '8px', textAlign: 'left' }}>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {reviews.map((review) => (
                                    <tr key={review.reviewId} style={{ borderBottom: '1px solid #eee' }}>
                                        <td style={{ padding: '8px' }}>{review.reviewId}</td>
                                        <td style={{ padding: '8px' }}>{review.productId}</td>
                                        <td style={{ padding: '8px' }}>{review.reviewText.substring(0, 150)}{review.reviewText.length > 150 ? '...' : ''}</td>
                                        <td style={{ padding: '8px' }}>{review.abuseReason}</td>
                                        <td style={{ padding: '8px' }}>{new Date(review.flaggedTimestamp).toLocaleString()}</td>
                                        <td style={{ padding: '8px' }}>
                                            <button onClick={() => console.log('View details for', review.reviewId)} style={{ marginRight: '5px' }}>View Details</button>
                                            <button onClick={() => handleMarkAsAbusive(review.reviewId)}>Mark as Abusive</button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            );
        }

        export default FlaggedReviewsDashboard;
        ```

#### User Story 4: Manual Review Flagging (28 hours)

*   **Task 4.1: Design the user interface element (e.g., button, input field for reason) for analysts to manually flag a review.**
    *   **Implementation Plan:** On the `FlaggedReviewsDashboard`, add a "Mark as Abusive" button for each review. Clicking this button will trigger a JavaScript `prompt` (or a more sophisticated modal in a full implementation) asking the analyst for a reason. This reason will be sent to the backend API.
    *   **UI Elements:** Button, simple text input (prompt) for reason.

*   **Task 4.2: Develop the backend API endpoint to allow an analyst to update a review's status to "abusive" and record a specific reason.**
    *   **Implementation Plan:** Create an AWS API Gateway REST API endpoint: `PUT /reviews/{reviewId}/status`. This endpoint will trigger an AWS Lambda function ('''UpdateReviewStatusLambda'''). The Lambda will receive the `reviewId` from the path and the new `status` ("ABUSIVE") and `reason` (analyst's input) from the request body. It will update the corresponding review in the `Reviews` DynamoDB table, setting `status` to "ABUSIVE", `manualAbuseReason` to the provided reason, `abusedByAnalystId` (from authentication context, or a placeholder for this sprint), and `manualFlaggingTimestamp`.
    *   **Technical Decisions:** API Gateway with PUT method, Lambda for update logic, DynamoDB for data persistence.
    *   **Code Snippet (Pseudocode for `UpdateReviewStatusLambda`):**
        ```python
        import json
        import time
        # import boto3 # For actual DynamoDB client

        # dynamodb = boto3.resource('dynamodb')
        # reviews_table = dynamodb.Table('Reviews')

        def update_review_status_lambda(event, context):
            try:
                review_id = event['pathParameters']['reviewId']
                body = json.loads(event['body'])
                
                new_status = body.get('status')
                manual_abuse_reason = body.get('reason', 'No reason provided.')
                analyst_id = body.get('analystId', 'anonymous_analyst') # In real system, derived from auth

                if new_status not in ['ABUSIVE']:
                    return {
                        'statusCode': 400,
                        'headers': {'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'message': 'Invalid status provided. Only "ABUSIVE" is allowed for manual flagging.'})
                    }

                # Update item in DynamoDB
                # response = reviews_table.update_item(
                #     Key={'reviewId': review_id},
                #     UpdateExpression="SET #s = :s, manualAbuseReason = :mar, abusedByAnalystId = :abai, manualFlaggingTimestamp = :mft",
                #     ExpressionAttributeNames={'#s': 'status'},
                #     ExpressionAttributeValues={
                #         ':s': new_status,
                #         ':mar': manual_abuse_reason,
                #         ':abai': analyst_id,
                #         ':mft': int(time.time() * 1000)
                #     }
                # )
                
                print(f"Review {review_id} manually marked as {new_status} by {analyst_id}. Reason: {manual_abuse_reason}")

                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'message': f'Review {review_id} status updated to {new_status}.'})
                }
            except Exception as e:
                print(f"Error updating review status: {e}. Event: {event}")
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'message': 'Failed to update review status.'})
                }
        ```

*   **Task 4.3: Implement the front-end logic to integrate the manual flagging UI element with the backend API.**
    *   **Implementation Plan:** The `handleMarkAsAbusive` function in the `FlaggedReviewsDashboard.js` React component (as shown in Task 3.3) will be implemented. This function will make a `PUT` request to the `PUT /reviews/{reviewId}/status` API endpoint, sending the new status and the analyst's reason. After a successful update, the dashboard will be refreshed to reflect the change.
    *   **Technical Decisions:** JavaScript `fetch` API to interact with the backend API.
