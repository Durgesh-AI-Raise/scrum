## Sprint Goal: "Establish the initial end-to-end pipeline for real-time ingestion of Amazon review data, develop and integrate the first iteration of individual review abuse detection models, and provide Trust & Safety Analysts with a secure dashboard to view flagged individual reviews."

---

## 1) Implementation Plan, Data Models & Architecture, Assumptions, Technical Decisions, and Code Snippets

### User Story: P1-US1 - Ingest Review Data in Near Real-time

**Overall Goal:** Establish the initial end-to-end pipeline for real-time ingestion of Amazon review data.

#### Task 1.1: Design Streaming Data Ingestion Architecture
*   **Implementation Plan:** Design a cloud-native, scalable streaming architecture. This involves identifying data sources (e.g., Amazon Product Advertising API, controlled web scraping for reviews; internal systems for reviewer profiles), selecting a streaming platform (e.g., AWS Kinesis, Apache Kafka), defining data formats (JSON for flexibility, potentially Avro for schema evolution), and initial storage for raw data (AWS S3 Data Lake).
*   **Data Models:**
    *   `ReviewData` (Incoming): `reviewId` (string), `productId` (string), `userId` (string), `rating` (int), `title` (string), `text` (string), `reviewDate` (timestamp), `sourceSystem` (string).
    *   `ReviewerData` (Incoming): `userId` (string), `userName` (string), `accountAge` (int, in days), `purchaseHistory` (list of objects: `{productId: string, purchaseDate: timestamp}`), `isPrimeMember` (boolean).
*   **Architecture:**
    *   **Data Sources:** Amazon API Gateway/Lambda (for controlled access to Amazon data), existing internal user databases.
    *   **Ingestion Layer (Streaming):** AWS Kinesis Data Streams (e.g., `amazon-reviews-stream`, `amazon-reviewers-stream`).
    *   **Processing Layer (Optional Real-time Transformation):** AWS Kinesis Data Analytics (for minor schema enforcement, basic filtering, or joining streams).
    *   **Raw Data Storage:** AWS S3 Data Lake (e.g., `s3://trust-safety-raw-data/`).
*   **Assumptions/Technical Decisions:**
    *   Amazon review data access is feasible either through a public API with rate limits or via controlled, ethical web scraping.
    *   Reviewer data is available from an existing internal system via an API or database export.
    *   AWS managed services are preferred for rapid prototyping and scalability.
    *   Initial data format for streams will be JSON for ease of development.
*   **Code Snippets/Pseudocode:** N/A (Architecture design task).

#### Task 1.2: Implement Review Data Ingestion Pipeline
*   **Implementation Plan:** Develop a Python-based producer application that periodically fetches new Amazon product reviews. This application will parse the review data into the `ReviewData` model and publish each review as a JSON message to the `amazon-reviews-stream` Kinesis stream, using `reviewId` as the partition key.
*   **Data Models:** `ReviewData` as defined in Task 1.1.
*   **Architecture:** Python application (deployed as an AWS Lambda function or on EC2/ECS) acting as a Kinesis producer.
*   **Assumptions/Technical Decisions:**
    *   A mechanism to track the last ingested review (e.g., last `reviewDate`) is implemented to prevent re-ingestion.
    *   Error handling and retry mechanisms for API calls and Kinesis `put_record` operations are included.
*   **Code Snippets/Pseudocode:**
    ```python
    import json
    import boto3
    from datetime import datetime

    # Initialize Kinesis client
    kinesis_client = boto3.client('kinesis', region_name='us-east-1') # Replace with your region

    def fetch_amazon_reviews(api_client, last_ingested_date):
        """
        Placeholder function to simulate fetching new Amazon reviews.
        In a real scenario, this would call an Amazon API or scraper.
        """
        print(f"Fetching reviews newer than: {last_ingested_date}")
        # Simulate fetching new reviews
        new_reviews = [
            {
                "reviewId": "R12345",
                "productId": "P001",
                "userId": "U001",
                "rating": 5,
                "title": "Great Product!",
                "text": "I really enjoyed using this product. Highly recommend.",
                "reviewDate": datetime.now().isoformat(),
                "sourceSystem": "Amazon"
            },
            {
                "reviewId": "R12346",
                "productId": "P002",
                "userId": "U002",
                "rating": 1,
                "title": "Terrible experience",
                "text": "This product broke after one use. Very disappointed.",
                "reviewDate": datetime.now().isoformat(),
                "sourceSystem": "Amazon"
            }
        ]
        return new_reviews

    def publish_review_to_stream(review_data: dict):
        """
        Publishes a single review record to the Kinesis stream.
        """
        try:
            json_data = json.dumps(review_data)
            response = kinesis_client.put_record(
                StreamName='amazon-reviews-stream', # Your Kinesis stream name
                Data=json_data,
                PartitionKey=review_data['reviewId']
            )
            print(f"Successfully published review {review_data['reviewId']} to Kinesis. SequenceNumber: {response['SequenceNumber']}")
        except Exception as e:
            print(f"Error publishing review {review_data['reviewId']}: {e}")

    def main_review_ingestion_pipeline(event, context):
        """
        Main entry point for the review ingestion Lambda/application.
        """
        # Load last ingested date from a persistent store (e.g., S3, DynamoDB)
        last_ingested_date = "2023-01-01T00:00:00Z" # Placeholder

        reviews_to_ingest = fetch_amazon_reviews(None, last_ingested_date) # api_client placeholder
        for review in reviews_to_ingest:
            publish_review_to_stream(review)

        # Update last ingested date
        print("Review ingestion pipeline completed.")

    ```

#### Task 1.3: Implement Reviewer Data Ingestion Pipeline
*   **Implementation Plan:** Develop a Python-based producer application to fetch associated reviewer data. This pipeline will either be triggered by new `userId`s identified in the review stream (e.g., via a Kinesis Data Analytics aggregation) or by periodically fetching updates for known `userId`s from internal systems. It will publish `ReviewerData` as JSON messages to the `amazon-reviewers-stream` Kinesis stream, using `userId` as the partition key.
*   **Data Models:** `ReviewerData` as defined in Task 1.1.
*   **Architecture:** Similar to Task 1.2, a Python application (Lambda/EC2/ECS) acting as a Kinesis producer.
*   **Assumptions/Technical Decisions:**
    *   Internal API/database for reviewer data is robust and performant.
    *   Incremental updates for reviewer data are handled efficiently.
*   **Code Snippets/Pseudocode:**
    ```python
    import json
    import boto3
    from datetime import datetime

    kinesis_client = boto3.client('kinesis', region_name='us-east-1')

    def fetch_reviewer_data(internal_api_client, user_id):
        """
        Placeholder function to simulate fetching reviewer data.
        In a real scenario, this would call an internal API.
        """
        print(f"Fetching reviewer data for user: {user_id}")
        # Simulate fetching data for a given user ID
        if user_id == "U001":
            return {
                "userId": "U001",
                "userName": "JohnDoe",
                "accountAge": 730, # 2 years
                "purchaseHistory": [
                    {"productId": "P001", "purchaseDate": "2023-03-15T10:00:00Z"},
                    {"productId": "P003", "purchaseDate": "2023-02-01T09:00:00Z"}
                ],
                "isPrimeMember": True
            }
        return None

    def publish_reviewer_to_stream(reviewer_data: dict):
        """
        Publishes a single reviewer record to the Kinesis stream.
        """
        try:
            json_data = json.dumps(reviewer_data)
            response = kinesis_client.put_record(
                StreamName='amazon-reviewers-stream', # Your Kinesis stream name
                Data=json_data,
                PartitionKey=reviewer_data['userId']
            )
            print(f"Successfully published reviewer {reviewer_data['userId']} to Kinesis. SequenceNumber: {response['SequenceNumber']}")
        except Exception as e:
            print(f"Error publishing reviewer {reviewer_data['userId']}: {e}")

    def main_reviewer_ingestion_pipeline(event, context):
        """
        Main entry point for the reviewer ingestion Lambda/application.
        Could be triggered by new user IDs from review stream or a schedule.
        """
        # Example: Ingest data for a specific user, or a batch of users
        user_ids_to_ingest = ["U001", "U002"] # From a queue or previous processing step

        for user_id in user_ids_to_ingest:
            reviewer_info = fetch_reviewer_data(None, user_id) # internal_api_client placeholder
            if reviewer_info:
                publish_reviewer_to_stream(reviewer_info)
        print("Reviewer ingestion pipeline completed.")

    ```

#### Task 1.4: Set Up Raw Data Storage
*   **Implementation Plan:** Configure an AWS S3 bucket as the raw data lake. Utilize AWS Kinesis Firehose to automatically consume data from `amazon-reviews-stream` and `amazon-reviewers-stream` and deliver it to S3. Data will be stored in raw JSON format, partitioned by ingestion date (`year/month/day/hour`) for efficient querying.
*   **Data Models:** Raw JSON objects as ingested for both `ReviewData` and `ReviewerData`.
*   **Architecture:** AWS S3, AWS Kinesis Firehose.
*   **Assumptions/Technical Decisions:**
    *   S3 is cost-effective and scalable for raw data storage.
    *   Kinesis Firehose simplifies the process of moving streaming data to S3 without managing consumers.
    *   Standard S3 security (encryption, access policies) will be applied.
*   **Code Snippets/Pseudocode:** (Conceptual setup via Infrastructure as Code like CloudFormation/Terraform, not directly Python code)
    ```yaml
    # Example CloudFormation Snippet for Kinesis Firehose to S3
    Resources:
      RawReviewsS3Bucket:
        Type: AWS::S3::Bucket
        Properties:
          BucketName: trust-safety-raw-reviews-data
          # ... other S3 bucket properties like encryption, lifecycle policies

      ReviewDataFirehoseStream:
        Type: AWS::KinesisFirehose::DeliveryStream
        Properties:
          DeliveryStreamName: ReviewDataToS3Firehose
          DeliveryStreamType: KinesisStreamAsSource
          KinesisStreamSourceConfiguration:
            KinesisStreamARN: !GetAtt amazon-reviews-stream.Arn # ARN of your Kinesis Stream
            RoleARN: !GetAtt FirehoseRole.Arn # IAM Role for Firehose
          ExtendedS3DestinationConfiguration:
            BucketARN: !GetAtt RawReviewsS3Bucket.Arn
            Prefix: raw/reviews/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/
            ErrorOutputPrefix: errors/reviews/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/
            BufferingHints:
              IntervalInSeconds: 300
              SizeInMBs: 5
            CompressionFormat: GZIP
            # ... other S3 destination configuration
            RoleARN: !GetAtt FirehoseRole.Arn
    ```

#### Task 1.5: Develop Data Ingestion Monitoring
*   **Implementation Plan:** Implement monitoring using AWS CloudWatch for key metrics of Kinesis streams (e.g., `IncomingBytes`, `IncomingRecords`, `ReadProvisionedThroughputExceeded`, `WriteProvisionedThroughputExceeded`). Configure CloudWatch Alarms to trigger SNS notifications for critical issues. Implement custom metrics in producer applications for data volume and latency, and send application logs to CloudWatch Logs.
*   **Data Models:** N/A (focus on operational metrics and logs).
*   **Architecture:** AWS CloudWatch, AWS SNS.
*   **Assumptions/Technical Decisions:**
    *   CloudWatch provides sufficient basic monitoring for the initial sprint.
    *   Alerts will be sent to an SNS topic, which can then notify a team (e.g., via email or Slack integration).
*   **Code Snippets/Pseudocode:** (Conceptual CloudWatch Alarm setup via CloudFormation/Terraform)
    ```yaml
    # Example CloudFormation Snippet for Kinesis CloudWatch Alarm
    Resources:
      KinesisReviewsIncomingRecordsAlarm:
        Type: AWS::CloudWatch::Alarm
        Properties:
          AlarmName: HighKinesisReviewsIncomingRecords
          ComparisonOperator: GreaterThanThreshold
          EvaluationPeriods: 1
          MetricName: IncomingRecords
          Namespace: AWS/Kinesis
          Period: 300 # 5 minutes
          Statistic: Sum
          Threshold: 1000 # Example: more than 1000 records in 5 minutes
          TreatMissingData: notBreaching
          AlarmActions:
            - !Ref IngestionAlertsSnsTopic # ARN of your SNS Topic
          Dimensions:
            - Name: StreamName
              Value: amazon-reviews-stream
          AlarmDescription: "Alarm when the incoming record count for amazon-reviews-stream is too high, indicating a surge."
    ```

---

### User Story: P1-US2 - Develop Initial ML Models for Individual Reviews

**Overall Goal:** Develop and integrate the first iteration of individual review abuse detection models.

#### Task 2.1: Research & Select Initial ML Algorithms for Individual Reviews
*   **Implementation Plan:** Research will focus on straightforward, interpretable models.
    *   **Keyword Stuffing:** Rule-based detection using regex or exact keyword matching.
    *   **Unusual Rating Patterns (by Reviewer):** Simple statistical anomaly detection (e.g., Z-score, IQR) on reviewer's average rating deviation or review velocity.
    *   **Basic Sentiment Analysis:** Leveraging pre-trained models or training a simple classifier (e.g., Logistic Regression with TF-IDF features) to detect extreme sentiment that might indicate manipulation.
    *   **Overall Anomaly Detection:** Potentially Isolation Forest or One-Class SVM on combined textual and numerical features.
    *   **Proposed Approach:** A hybrid model combining rule-based flags for obvious patterns and a simple supervised classifier (e.g., Logistic Regression or a small Gradient Boosting model) on engineered features from review text (TF-IDF) and reviewer behavior (e.g., account age, review count, average rating).
*   **Data Models:** N/A (Research task).
*   **Architecture:** Conceptual, focusing on algorithm selection.
*   **Assumptions/Technical Decisions:**
    *   Initial models prioritize precision to minimize false positives for analysts, even if it means lower recall.
    *   Interpretability is important for trust and iteration.
    *   Python-based ML libraries (Scikit-learn, NLTK) will be used.
*   **Code Snippets/Pseudocode:** N/A (Research task, output is documentation).

#### Task 2.2: Prepare Training/Test Datasets for Individual Review Flagging
*   **Implementation Plan:**
    1.  **Data Extraction:** Query processed review and reviewer data from the S3 Data Lake (or a curated data warehouse if available).
    2.  **Text Preprocessing:** Clean review text (remove HTML, special characters, normalize case, tokenization).
    3.  **Feature Engineering (Text):** Apply TF-IDF or Word2Vec embeddings to review text.
    4.  **Feature Engineering (Reviewer):** Extract numerical features from reviewer data (e.g., `accountAge`, `reviewCount`, `averageRating`, `purchaseFrequency`). Scale numerical features (StandardScaler).
    5.  **Labeling:** For the initial model, leverage rule-based labeling (e.g., reviews containing known spam phrases, reviews from accounts with suspicious activity flags) to create a bootstrapped training set. A small set of manually labeled data can augment this if available.
    6.  **Dataset Split:** Split the combined feature set into training, validation, and test sets.
*   **Data Models:**
    *   `FeatureSet`: `reviewId` (string), `text_features` (vector), `reviewer_numerical_features` (vector), `label` (int: 0=legit, 1=abusive).
*   **Architecture:** Data processing pipeline using PySpark (for large scale) or Pandas (for smaller scale) running on a managed service (e.g., AWS Glue, EC2 instance).
*   **Assumptions/Technical Decisions:**
    *   A sufficient volume of historical data is available in the data lake.
    *   Initial labeling strategy is a combination of rule-based heuristics and potentially a small amount of human-labeled data.
    *   Standard feature engineering techniques are sufficient.
*   **Code Snippets/Pseudocode:**
    ```python
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import re
    import joblib # To save vectorizer and scaler

    def clean_text(text):
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', '', text) # Remove special characters
        return text

    def prepare_datasets(df_reviews_raw: pd.DataFrame, df_reviewers_raw: pd.DataFrame):
        # Assuming df_reviews_raw has 'reviewId', 'text', 'userId', 'rating', 'reviewDate'
        # Assuming df_reviewers_raw has 'userId', 'accountAge', 'purchaseHistory'

        # 1. Clean review text
        df_reviews_raw['cleaned_text'] = df_reviews_raw['text'].apply(clean_text)

        # 2. Merge dataframes
        # For simplicity, let's assume reviewer data is joined per reviewId
        # In reality, you'd join based on userId from the review and enrich with reviewer specific aggregate features.
        df_merged = pd.merge(df_reviews_raw, df_reviewers_raw, on='userId', how='left')

        # 3. Feature Engineering - Text (TF-IDF)
        tfidf_vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        tfidf_features = tfidf_vectorizer.fit_transform(df_merged['cleaned_text']).toarray()
        tfidf_df = pd.DataFrame(tfidf_features, columns=[f'tfidf_{i}' for i in range(tfidf_features.shape[1])])

        # 4. Feature Engineering - Reviewer Numerical Features
        # Example: calculate review count for each user based on historical data
        df_merged['review_count'] = df_merged.groupby('userId')['reviewId'].transform('count')
        # Fill missing accountAge with a default or mean
        df_merged['accountAge'].fillna(df_merged['accountAge'].median(), inplace=True)

        numerical_features_to_scale = ['accountAge', 'review_count']
        scaler = StandardScaler()
        df_merged[numerical_features_to_scale] = scaler.fit_transform(df_merged[numerical_features_to_scale])

        # Combine all features
        X = pd.concat([tfidf_df, df_merged[numerical_features_to_scale]], axis=1)

        # 5. Labeling (Rule-based for initial bootstrapping)
        # Example: Label as 1 (abusive) if text contains suspicious keywords or very low rating from a new account
        df_merged['label'] = 0
        df_merged.loc[df_merged['cleaned_text'].str.contains('buy fake reviews|guaranteed 5 star') |
                      ((df_merged['rating'] <= 2) & (df_merged['accountAge'] < 30) & (df_merged['review_count'] == 1)), 'label'] = 1

        y = df_merged['label']

        # 6. Split dataset
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        # Save preprocessors for inference
        joblib.dump(tfidf_vectorizer, 'tfidf_vectorizer.pkl')
        joblib.dump(scaler, 'feature_scaler.pkl')

        return X_train, X_test, y_train, y_test

    ```

#### Task 2.3: Implement & Train Initial ML Model (Individual Reviews)
*   **Implementation Plan:** Implement the chosen ML model (e.g., Logistic Regression) using Scikit-learn. Train the model on the prepared `X_train` and `y_train` datasets. Evaluate the model's performance on `X_test` and `y_test` using metrics like precision, recall, F1-score, and AUC. Save the trained model artifact (e.g., using `joblib`).
*   **Data Models:** Serialized model artifact (`.pkl` file).
*   **Architecture:** ML training script running on a compute instance (e.g., EC2, SageMaker Notebook).
*   **Assumptions/Technical Decisions:**
    *   The model will be trained in a reproducible environment.
    *   Version control for model code and tracking for model artifacts (e.g., MLflow, S3 for storage).
*   **Code Snippets/Pseudocode:**
    ```python
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, roc_auc_score
    import joblib
    import pandas as pd
    # Assume X_train, X_test, y_train, y_test are available from Task 2.2

    def train_and_evaluate_model(X_train: pd.DataFrame, X_test: pd.DataFrame, y_train: pd.Series, y_test: pd.Series):
        print("Training Logistic Regression model...")
        model = LogisticRegression(solver='liblinear', random_state=42, class_weight='balanced') # Use class_weight for imbalanced data
        model.fit(X_train, y_train)
        print("Model training complete.")

        # Evaluate on test set
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        print("\n--- Model Evaluation ---")
        print(classification_report(y_test, y_pred))
        print(f"ROC AUC Score: {roc_auc_score(y_test, y_proba)}")

        # Save the trained model
        model_filename = 'initial_abuse_detection_model.pkl'
        joblib.dump(model, model_filename)
        print(f"Model saved as {model_filename}")

        return model

    # Example usage (assuming X_train, X_test, y_train, y_test are loaded/generated)
    # df_reviews = pd.DataFrame(...) # Load dummy/real data
    # df_reviewers = pd.DataFrame(...) # Load dummy/real data
    # X_train, X_test, y_train, y_test = prepare_datasets(df_reviews, df_reviewers)
    # trained_model = train_and_evaluate_model(X_train, X_test, y_train, y_test)

    ```

#### Task 2.4: Integrate ML Model for Real-time Scoring
*   **Implementation Plan:** Deploy the trained model and associated preprocessors (TF-IDF vectorizer, scaler) as an inference service (e.g., using AWS SageMaker Endpoints, or a containerized FastAPI service on ECS/EKS). A consumer application (e.g., AWS Lambda triggered by Kinesis `amazon-reviews-stream`) will:
    1.  Read incoming review data from the stream.
    2.  Fetch corresponding reviewer data (e.g., from a fast lookup database like DynamoDB which mirrors processed reviewer data).
    3.  Preprocess the data for the model (clean text, transform with TF-IDF vectorizer, scale numerical features).
    4.  Invoke the ML inference service to get a prediction (flagging status and confidence score).
    5.  Store the scored review data (including `reviewId`, `flaggingStatus`, `confidenceScore`, `scoringTimestamp`) in a designated database (e.g., DynamoDB table `FlaggedReviews`).
*   **Data Models:**
    *   `ScoredReview`: `reviewId` (string), `flaggingStatus` (boolean), `confidenceScore` (float), `modelUsed` (string), `scoringTimestamp` (timestamp), `reviewerId` (string), `productId` (string), `reviewTextSnippet` (string).
*   **Architecture:** Kinesis Stream -> Lambda (consumer) -> ML Inference Service (FastAPI/SageMaker) -> DynamoDB (for flagged reviews).
*   **Assumptions/Technical Decisions:**
    *   The ML inference service is designed for low-latency predictions.
    *   DynamoDB is chosen for its fast read/write capabilities for individual items.
    *   Reviewer data for real-time scoring is readily available (e.g., denormalized or in a low-latency cache).
*   **Code Snippets/Pseudocode:** (Conceptual Lambda function)
    ```python
    import json
    import boto3
    import requests # For calling ML prediction API
    import joblib # To load preprocessors (tfidf_vectorizer, scaler)
    from datetime import datetime
    import pandas as pd
    import re

    # Load preprocessors and model (if embedding in Lambda)
    # tfidf_vectorizer = joblib.load('tfidf_vectorizer.pkl')
    # scaler = joblib.load('feature_scaler.pkl')
    # model = joblib.load('initial_abuse_detection_model.pkl')

    ML_API_ENDPOINT = "http://your-ml-inference-service.com/predict_review"
    DYNAMODB_TABLE_NAME = "FlaggedReviews"

    dynamodb_client = boto3.resource('dynamodb', region_name='us-east-1')
    flagged_reviews_table = dynamodb_client.Table(DYNAMODB_TABLE_NAME)

    # Re-use preprocessing functions from Task 2.2
    def clean_text(text):
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return text

    def lambda_handler(event, context):
        for record in event['Records']:
            payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            review_data = json.loads(payload)

            review_id = review_data.get('reviewId')
            user_id = review_data.get('userId')
            review_text = review_data.get('text')
            product_id = review_data.get('productId')
            review_date = review_data.get('reviewDate')
            rating = review_data.get('rating')

            # --- Fetch Reviewer Data (Placeholder) ---
            # In a real system, query DynamoDB or cache for reviewer data using user_id
            reviewer_data = {
                'userId': user_id,
                'accountAge': 365, # Example value
                'review_count': 5  # Example value
            }

            if not review_id or not user_id or not review_text:
                print(f"Skipping malformed record: {review_data}")
                continue

            # --- Prepare Features for ML Model ---
            cleaned_text = clean_text(review_text)

            # In a real scenario, you would pass these to the ML API
            # For this example, let's assume the ML API handles full text and reviewer features
            ml_input = {
                "review_text": cleaned_text,
                "account_age_days": reviewer_data['accountAge'],
                "review_count": reviewer_data['review_count'],
                "rating": rating
                # ... other features
            }

            try:
                # --- Invoke ML Prediction API ---
                response = requests.post(ML_API_ENDPOINT, json=ml_input)
                response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
                prediction = response.json()

                flagging_status = prediction.get('flagged', False)
                confidence_score = prediction.get('score', 0.0)
                model_version = prediction.get('model_version', 'v1.0') # Assuming API returns version

                # --- Store Scored Review ---
                if flagging_status:
                    item_to_store = {
                        'reviewId': review_id,
                        'flaggingStatus': flagging_status,
                        'confidenceScore': confidence_score,
                        'modelUsed': model_version,
                        'scoringTimestamp': datetime.utcnow().isoformat(),
                        'reviewerId': user_id,
                        'productId': product_id,
                        'reviewTextSnippet': review_text[:200], # Store a snippet for dashboard quick view
                        'reviewDate': review_date,
                        'rating': rating
                    }
                    flagged_reviews_table.put_item(Item=item_to_store)
                    print(f"Flagged review {review_id} with score {confidence_score:.2f}")
                else:
                    print(f"Review {review_id} not flagged (score: {confidence_score:.2f})")

            except requests.exceptions.RequestException as e:
                print(f"Error calling ML API for review {review_id}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred for review {review_id}: {e}")

        return {'statusCode': 200, 'body': json.dumps('Processing complete!')}

    ```

#### Task 2.5: Develop ML Prediction API Endpoint
*   **Implementation Plan:** Develop a RESTful API using FastAPI (Python). This API will:
    1.  Load the trained ML model and preprocessors (TF-IDF vectorizer, scaler) into memory upon service startup.
    2.  Define an endpoint (e.g., `/predict_review`) that accepts new review and reviewer data.
    3.  Preprocess the incoming data using the loaded preprocessors.
    4.  Perform inference using the loaded ML model.
    5.  Return the prediction (e.g., `flagged: true/false`, `score: 0.0-1.0`) and optionally the model version.
*   **Data Models:**
    *   **Request (`ReviewPredictionRequest`):** `review_text` (string), `account_age_days` (int), `review_count` (int), `rating` (int), etc.
    *   **Response (`ReviewPredictionResponse`):** `flagged` (boolean), `score` (float), `model_version` (string).
*   **Architecture:** FastAPI application deployed as a Docker container on AWS ECS/EKS, or potentially AWS Lambda with provisioned concurrency for performance.
*   **Assumptions/Technical Decisions:**
    *   The API needs to be performant and highly available.
    *   Model and preprocessors are loaded once at startup for efficiency.
    *   Security measures (e.g., API Gateway with authentication/authorization) will protect the endpoint.
*   **Code Snippets/Pseudocode:**
    ```python
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import joblib
    import pandas as pd
    import re
    import os

    app = FastAPI()

    # Load model and preprocessors globally on startup
    # In a real deployment, these files would be mounted from S3 or an EFS volume.
    try:
        model = joblib.load('initial_abuse_detection_model.pkl')
        tfidf_vectorizer = joblib.load('tfidf_vectorizer.pkl')
        scaler = joblib.load('feature_scaler.pkl')
        print("ML Model and preprocessors loaded successfully.")
    except Exception as e:
        print(f"Error loading ML assets: {e}")
        # In a production setup, you might want to raise an exception and prevent startup
        model, tfidf_vectorizer, scaler = None, None, None # Set to None for graceful error handling

    class ReviewPredictionRequest(BaseModel):
        review_text: str
        account_age_days: int
        review_count: int
        rating: int
        # Add other features used by the model

    class ReviewPredictionResponse(BaseModel):
        flagged: bool
        score: float
        model_version: str = "v1.0" # Hardcoded for initial version

    def clean_text_for_inference(text):
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return text

    @app.post("/predict_review", response_model=ReviewPredictionResponse)
    async def predict_review(request: ReviewPredictionRequest):
        if model is None or tfidf_vectorizer is None or scaler is None:
            raise HTTPException(status_code=500, detail="ML Model not loaded.")

        # 1. Preprocess review text
        cleaned_text = clean_text_for_inference(request.review_text)
        tfidf_features = tfidf_vectorizer.transform([cleaned_text]).toarray()
        tfidf_df = pd.DataFrame(tfidf_features, columns=[f'tfidf_{i}' for i in range(tfidf_features.shape[1])])

        # 2. Prepare numerical reviewer features
        numerical_data = pd.DataFrame([[request.account_age_days, request.review_count]],
                                      columns=['accountAge', 'review_count'])
        scaled_numerical_features = scaler.transform(numerical_data)
        scaled_numerical_df = pd.DataFrame(scaled_numerical_features, columns=['accountAge', 'review_count'])

        # 3. Combine all features
        # Ensure feature order and count match training data
        input_features = pd.concat([tfidf_df, scaled_numerical_df], axis=1)

        # 4. Perform prediction
        prediction_proba = model.predict_proba(input_features)[0][1] # Probability of being class 1 (abusive)
        flagged_status = bool(model.predict(input_features)[0]) # Convert numpy bool to native bool

        return ReviewPredictionResponse(
            flagged=flagged_status,
            score=float(prediction_proba) # Ensure float type
        )

    # To run this FastAPI app: uvicorn prediction_api:app --host 0.0.0.0 --port 8000
    ```

---

### User Story: P1-US4 - Display Flagged Individual Reviews in Dashboard

**Overall Goal:** Provide Trust & Safety Analysts with a secure dashboard to view flagged individual reviews.

#### Task 3.1: Design Basic UI/UX for Flagged Individual Reviews Display
*   **Implementation Plan:** Design wireframes for a simple, responsive web dashboard. The main view will be a table listing flagged reviews. Key information per review: `Review ID`, `Review Text Snippet`, `Confidence Score` (prominently displayed and sortable), `Reviewer ID`, `Review Date`, `Product ID`. Include filters for date range, minimum confidence score, and search by review/product/reviewer ID. Prioritization will be implicit through sorting by confidence score (highest first).
*   **Data Models:** N/A (UI/UX design task, output is wireframes/mockups).
*   **Architecture:** Frontend design principles.
*   **Assumptions/Technical Decisions:**
    *   Dashboard will be a Single Page Application (SPA).
    *   The design prioritizes functionality and clarity for Trust & Safety Analysts.
*   **Code Snippets/Pseudocode:** N/A (UI/UX design task).

#### Task 3.2: Develop Backend Service for Flagged Individual Reviews
*   **Implementation Plan:** Develop a backend RESTful API service (e.g., using FastAPI or Node.js/Express) that interacts with the `FlaggedReviews` DynamoDB table (from Task 2.4). This service will provide an endpoint (e.g., `/api/flagged_reviews`) to:
    1.  Query the `FlaggedReviews` table, retrieving items based on filters (e.g., date range).
    2.  Sort the results primarily by `confidenceScore` in descending order.
    3.  Implement pagination to handle large result sets.
    4.  Aggregate and enrich data if necessary (e.g., fetch full review text from S3 if only a snippet is in DynamoDB, or join with product/reviewer metadata if available in other fast databases).
*   **Data Models:**
    *   **Request (GET `/api/flagged_reviews` query params):** `limit` (int), `offset` (int), `sortBy` (string, e.g., "confidenceScore", "reviewDate"), `sortOrder` (string, "asc", "desc").
    *   **Response (List of `FlaggedReviewItem`):** `reviewId` (string), `reviewText` (string), `confidenceScore` (float), `reviewerId` (string), `reviewerName` (string), `reviewDate` (timestamp), `productId` (string), `productTitle` (string), `rating` (int).
*   **Architecture:** FastAPI/Node.js service deployed on AWS Lambda + API Gateway, or AWS ECS/EKS.
*   **Assumptions/Technical Decisions:**
    *   DynamoDB Global Secondary Indexes (GSIs) will be used to support efficient queries and sorting on `confidenceScore` or `reviewDate`.
    *   The service should be highly available and responsive.
*   **Code Snippets/Pseudocode:**
    ```python
    from fastapi import FastAPI, Query, HTTPException, status
    from pydantic import BaseModel
    import boto3
    from boto3.dynamodb.conditions import Key, Attr
    from datetime import datetime, timedelta
    import json # For proper JSON serialization of Decimal from DynamoDB

    app = FastAPI()
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    flagged_reviews_table = dynamodb.Table('FlaggedReviews') # Table from Task 2.4

    class FlaggedReviewItem(BaseModel):
        reviewId: str
        reviewText: str
        confidenceScore: float
        reviewerId: str
        reviewerName: str # Enriched, might be placeholder
        reviewDate: str
        productId: str
        productTitle: str # Enriched, might be placeholder
        rating: int

    @app.get("/api/flagged_reviews", response_model=list[FlaggedReviewItem])
    async def get_flagged_reviews(
        limit: int = Query(20, ge=1, le=100),
        start_date: str = Query(None, description="Filter reviews from this date (YYYY-MM-DD)"),
        end_date: str = Query(None, description="Filter reviews up to this date (YYYY-MM-DD)"),
        min_confidence: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence score"),
        # DynamoDB pagination/sorting is complex. For simple sorting on score, we rely on a GSI
        # or scan and sort in memory for very small datasets.
        # For production, a GSI on `confidenceScore` as a partition key with `scoringTimestamp` as sort key could work.
        # For now, let's assume a simpler query or scan for demonstration.
    ):
        query_params = {
            'Limit': limit,
            'FilterExpression': Attr('confidenceScore').gte(min_confidence)
        }

        # Add date filtering if provided (assuming 'scoringTimestamp' is stored as ISO string)
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').isoformat()
                query_params['FilterExpression'] &= Attr('scoringTimestamp').gte(start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD.")
        if end_date:
            try:
                # Add one day to include the entire end_date
                end_dt = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)).isoformat()
                query_params['FilterExpression'] &= Attr('scoringTimestamp').lt(end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD.")

        try:
            # Perform a scan (for initial prototype, not for large datasets)
            # For production, use query with GSI or more advanced pagination if needed.
            response = flagged_reviews_table.scan(**query_params)
            items = response.get('Items', [])

            # Convert Decimal types from DynamoDB to float for Pydantic model
            for item in items:
                if 'confidenceScore' in item:
                    item['confidenceScore'] = float(item['confidenceScore'])
                if 'rating' in item:
                    item['rating'] = int(item['rating'])
                # Enrich with placeholder data for reviewerName, productTitle
                item['reviewerName'] = item.get('reviewerId', 'N/A') + "_User"
                item['productTitle'] = item.get('productId', 'N/A') + "_Product"

            # Sort by confidence score in descending order (in-memory for this scan example)
            sorted_items = sorted(items, key=lambda x: x.get('confidenceScore', 0.0), reverse=True)

            # Limit to requested amount
            return [FlaggedReviewItem(**item) for item in sorted_items[:limit]]

        except Exception as e:
            print(f"Error retrieving flagged reviews: {e}")
            raise HTTPException(status_code=500, detail="Internal server error while fetching reviews.")
    ```

#### Task 3.3: Implement Secure Front-end Dashboard (Individual Reviews)
*   **Implementation Plan:** Develop the frontend using a modern JavaScript framework (e.g., React). Implement:
    1.  **Dashboard Layout:** Basic header, sidebar, and main content area for the flagged reviews table.
    2.  **Table Component:** Display `FlaggedReviewItem`s in a tabular format. Enable client-side sorting by `Confidence Score` and `Review Date`, and basic pagination.
    3.  **Data Fetching:** Use `axios` or browser `fetch` to call the backend API (Task 3.2). Handle loading states and errors.
    4.  **UI Components:** Input fields for filters (date range, min confidence) and a search bar.
*   **Data Models:** Frontend components consume the `FlaggedReviewItem` model from the backend.
*   **Architecture:** React SPA served via AWS S3 + CloudFront for content delivery.
*   **Assumptions/Technical Decisions:**
    *   React is chosen for its component-based architecture and widespread adoption.
    *   Client-side routing will be handled.
    *   The dashboard will be served over HTTPS.
*   **Code Snippets/Pseudocode:**
    ```javascript
    // src/components/FlaggedReviewsList.js
    import React, { useState, useEffect } from 'react';
    import axios from 'axios';

    function FlaggedReviewsList() {
        const [reviews, setReviews] = useState([]);
        const [loading, setLoading] = useState(true);
        const [error, setError] = useState(null);
        const [minConfidence, setMinConfidence] = useState(0.5);
        const [startDate, setStartDate] = useState('');
        const [endDate, setEndDate] = useState('');

        useEffect(() => {
            fetchFlaggedReviews();
        }, [minConfidence, startDate, endDate]); // Re-fetch data when filters change

        const fetchFlaggedReviews = async () => {
            setLoading(true);
            setError(null);
            try {
                const params = {
                    min_confidence: minConfidence,
                    ...(startDate && { start_date: startDate }),
                    ...(endDate && { end_date: endDate }),
                    limit: 50 // Example limit
                };
                // Assuming the backend is running on the same host or proxied
                const response = await axios.get('/api/flagged_reviews', { params });
                setReviews(response.data);
            } catch (err) {
                console.error("Error fetching flagged reviews:", err);
                setError('Failed to load flagged reviews. Please try again.');
            } finally {
                setLoading(false);
            }
        };

        const handleFilterChange = (setter, value) => {
            setter(value);
        };

        if (loading) return <div className="text-center p-4">Loading flagged reviews...</div>;
        if (error) return <div className="text-red-500 text-center p-4">{error}</div>;

        return (
            <div className="container mx-auto p-4">
                <h1 className="text-2xl font-bold mb-4">Flagged Individual Reviews</h1>

                <div className="flex gap-4 mb-6 flex-wrap">
                    <label className="block">
                        Min Confidence:
                        <input
                            type="number"
                            step="0.01"
                            min="0"
                            max="1"
                            value={minConfidence}
                            onChange={(e) => handleFilterChange(setMinConfidence, e.target.value)}
                            className="ml-2 p-2 border rounded"
                        />
                    </label>
                    <label className="block">
                        Start Date:
                        <input
                            type="date"
                            value={startDate}
                            onChange={(e) => handleFilterChange(setStartDate, e.target.value)}
                            className="ml-2 p-2 border rounded"
                        />
                    </label>
                    <label className="block">
                        End Date:
                        <input
                            type="date"
                            value={endDate}
                            onChange={(e) => handleFilterChange(setEndDate, e.target.value)}
                            className="ml-2 p-2 border rounded"
                        />
                    </label>
                </div>

                {reviews.length === 0 ? (
                    <p>No flagged reviews found with the current filters.</p>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full bg-white border border-gray-300">
                            <thead>
                                <tr>
                                    <th className="py-2 px-4 border-b">Review ID</th>
                                    <th className="py-2 px-4 border-b">Review Text</th>
                                    <th className="py-2 px-4 border-b">Confidence Score</th>
                                    <th className="py-2 px-4 border-b">Reviewer ID</th>
                                    <th className="py-2 px-4 border-b">Review Date</th>
                                    <th className="py-2 px-4 border-b">Product ID</th>
                                </tr>
                            </thead>
                            <tbody>
                                {reviews.map((review) => (
                                    <tr key={review.reviewId} className="hover:bg-gray-50">
                                        <td className="py-2 px-4 border-b">{review.reviewId}</td>
                                        <td className="py-2 px-4 border-b">{review.reviewText.substring(0, 150)}...</td>
                                        <td className="py-2 px-4 border-b text-center">{(review.confidenceScore * 100).toFixed(2)}%</td>
                                        <td className="py-2 px-4 border-b">{review.reviewerId}</td>
                                        <td className="py-2 px-4 border-b">{new Date(review.reviewDate).toLocaleDateString()}</td>
                                        <td className="py-2 px-4 border-b">{review.productId}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        );
    }

    export default FlaggedReviewsList;
    ```

#### Task 3.4: Implement Basic Dashboard Authentication/Authorization
*   **Implementation Plan:** Implement authentication using AWS Cognito User Pools. The frontend will integrate with Cognito SDK for user signup, login, and session management. Upon successful authentication, a JWT token will be obtained. The backend API (Task 3.2) will be secured using JWT validation, ensuring that only authenticated users with the appropriate roles (e.g., "TrustAndSafetyAnalyst") can access the flagged reviews data.
*   **Data Models:** N/A (Authentication/Authorization task).
*   **Architecture:** AWS Cognito (User Pools, Identity Pools), JWT tokens for API authorization.
*   **Assumptions/Technical Decisions:**
    *   Cognito provides a secure, managed solution for user authentication.
    *   Role-Based Access Control (RBAC) will be implemented using Cognito user groups.
    *   All communication between frontend, Cognito, and backend APIs will be over HTTPS.
*   **Code Snippets/Pseudocode:** (Conceptual JWT validation in FastAPI backend)
    ```python
    from fastapi import FastAPI, Depends, HTTPException, status
    from fastapi.security import OAuth2PasswordBearer
    from jose import jwt, JWTError # python-jose library
    from pydantic import BaseModel
    import requests # To fetch JWKS keys
    from cachetools import cached, TTLCache

    # Assuming 'app' and 'FlaggedReviewItem' from Task 3.2 are already defined
    # app = FastAPI()
    # ... (other imports and model definitions)

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Assuming a /token endpoint for login (e.g., Cognito's endpoint)

    # Cognito User Pool configuration
    COGNITO_REGION = "us-east-1"
    COGNITO_USER_POOL_ID = "your_cognito_user_pool_id"
    COGNITO_JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"

    # Cache JWKS keys to avoid fetching them on every request
    jwks_cache = TTLCache(maxsize=1, ttl=3600) # Cache for 1 hour

    @cached(jwks_cache)
    def get_jwks():
        """Fetches and caches the JWKS keys from Cognito."""
        try:
            response = requests.get(COGNITO_JWKS_URL)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Could not fetch JWKS keys: {e}")

    async def get_current_user(token: str = Depends(oauth2_scheme)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            jwks = get_jwks()
            # Decode the token using the public keys from JWKS
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"], # Cognito uses RS256
                audience=os.environ.get("COGNITO_CLIENT_ID"), # Your Cognito App Client ID
                options={"verify_signature": True, "verify_aud": True, "verify_exp": True}
            )
            username: str = payload.get("cognito:username")
            user_roles: list = payload.get("cognito:groups", []) # Get user groups/roles
            if username is None:
                raise credentials_exception
        except JWTError as e:
            print(f"JWT validation error: {e}")
            raise credentials_exception
        except Exception as e:
            print(f"An unexpected error occurred during token validation: {e}")
            raise credentials_exception
        return {"username": username, "roles": user_roles}

    def verify_analyst_role(current_user: dict = Depends(get_current_user)):
        # Check if the user belongs to the 'TrustAndSafetyAnalyst' group
        if "TrustAndSafetyAnalyst" not in current_user["roles"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this resource. Requires 'TrustAndSafetyAnalyst' role."
            )
        return current_user

    # Protect the flagged_reviews endpoint with authentication and authorization
    @app.get("/api/flagged_reviews_secure", response_model=list[FlaggedReviewItem])
    async def get_flagged_reviews_secure(
        current_user: dict = Depends(verify_analyst_role), # This ensures auth and authz
        limit: int = Query(20, ge=1, le=100),
        start_date: str = Query(None, description="Filter reviews from this date (YYYY-MM-DD)"),
        end_date: str = Query(None, description="Filter reviews up to this date (YYYY-MM-DD)"),
        min_confidence: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence score"),
    ):
        print(f"User {current_user['username']} ({current_user['roles']}) accessed flagged reviews.")
        # Re-use the logic from the non-secure get_flagged_reviews endpoint in Task 3.2
        # Ensure to adapt it if original was not paginated/filtered properly for GSI
        return await get_flagged_reviews(limit=limit, start_date=start_date, end_date=end_date, min_confidence=min_confidence)

    ```