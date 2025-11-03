# Sprint 1 Planning: User Story 1 - Real-time Review Ingestion

**Sprint Goal:** To establish the foundational components of the Amazon Review Abuse Tracking System by implementing real-time review ingestion.

## User Story 1: As a system, I want to automatically ingest all new Amazon product reviews in real-time, so that the system has up-to-date data for analysis.

---

### Task 1.1: Research Amazon Review API/Scraping options

*   **Implementation Plan:**
    1.  Investigate official Amazon Product Advertising API (PA-API) for review data access. Check its capabilities, limitations, and terms of service regarding review content.
    2.  Research third-party Amazon review APIs (e.g., DataForSEO, ScrapeHero, Oxylabs) that might offer pre-built solutions for review data. Evaluate their cost, reliability, and data freshness.
    3.  Explore web scraping frameworks (e.g., Scrapy, BeautifulSoup with Requests in Python) for direct scraping of Amazon review pages. Understand the legal and ethical implications, rate limits, IP blocking risks, and effort required to maintain scrapers.
    4.  Document findings, including pros, cons, estimated cost, data fields accessible, and real-time capabilities for each option.
    5.  Recommend the most feasible and sustainable option for real-time ingestion.

*   **Data Models and Architecture:**
    *   No new data models are directly created in this research phase, but the output will inform the `Review` data model.
    *   Architecture consideration: The chosen ingestion method will be the first component of the data pipeline.

*   **Assumptions and Technical Decisions:**
    *   **Assumption:** There is a way to reliably obtain Amazon review data, either through an API or scraping, even if it requires effort.
    *   **Technical Decision (to be made after research):** Choose between official API, third-party API, or custom scraping. This choice will heavily influence subsequent tasks. For this plan, it's assumed that *some* method will be viable and chosen.

*   **Code Snippets/Pseudocode:**
    *   N/A for a research task. Output will be a research document.

---

### Task 1.2: Set up data pipeline for real-time ingestion

*   **Implementation Plan:**
    1.  **Select Ingestion Source:** Based on Task 1.1, decide on the concrete mechanism (e.g., Python script using a scraping library, API client using an SDK).
    2.  **Implement Data Collector:** Develop a service/script that continuously pulls new reviews from the source.
    3.  **Introduce Message Queue:** Publish raw review data to a message queue (e.g., Apache Kafka, AWS SQS/Kinesis) to decouple the ingestion process from downstream processing and provide buffering and fault tolerance.
    4.  **Set up Consumers:** Create a basic consumer that reads from the message queue and prints/logs the received data to confirm the pipeline is working.

*   **Data Models and Architecture:**
    *   **Architecture:**
        *   **Ingestion Service (Producer):** Responsible for fetching raw review data.
        *   **Message Queue (e.g., Kafka/Kinesis):** A buffer for raw review data.
        *   **Processing Service (Consumer - initial):** A simple service to read from the queue.
    *   **Data Model (Raw Review Data - preliminary):**
        ```python
        class RawReview:
            review_id: str
            product_asin: str
            reviewer_name: str
            review_text: str
            review_title: str
            rating: float
            review_date: str # Raw string initially
            helpfulness_votes: int
            # ... other fields available from source
        ```

*   **Assumptions and Technical Decisions:**
    *   **Assumption:** A message queuing system (Kafka, SQS, Kinesis) is available or can be easily set up.
    *   **Technical Decision:** Use Apache Kafka for its streaming capabilities and scalability. The ingestion service will be stateless as much as possible, relying on the message queue for persistence of raw events.
    *   **Technical Decision:** The ingestion frequency will be determined by the source's rate limits and the desired "real-time" definition (e.g., every 5 minutes, every hour).

*   **Code Snippets/Pseudocode:**
    ```python
    # Pseudocode for Ingestion Service (Producer)
    # Assumes a 'kafka_producer' client is configured
    def ingest_amazon_reviews():
        # Placeholder for fetching logic - will vary based on API/Scraping
        # Example: Using a hypothetical AmazonReviewsAPI client
        last_ingested_timestamp = get_last_ingested_timestamp_from_db() # Or from a state store
        new_reviews = AmazonReviewsAPI.fetch_new_reviews(since=last_ingested_timestamp)

        for review in new_reviews:
            raw_review_data = {
                "review_id": review.id,
                "product_asin": review.asin,
                "reviewer_name": review.reviewer_name,
                "review_text": review.text,
                "review_title": review.title,
                "rating": review.rating,
                "review_date": review.date, # Raw string as received
                "helpfulness_votes": review.helpfulness,
                "ingestion_timestamp": datetime.utcnow().isoformat() # Add system timestamp
            }
            kafka_producer.send("raw_amazon_reviews_topic", value=json.dumps(raw_review_data).encode('utf-8'))
            print(f"Published raw review: {review.id}")
        if new_reviews:
            update_last_ingested_timestamp_in_db(new_reviews[-1].date) # Update based on the latest review date

    # Pseudocode for a basic Consumer
    # Assumes a 'kafka_consumer' client is configured
    def process_raw_reviews_consumer():
        kafka_consumer.subscribe(["raw_amazon_reviews_topic"])
        while True:
            for message in kafka_consumer:
                raw_review = json.loads(message.value.decode('utf-8'))
                print(f"Received raw review (ID: {raw_review['review_id']}) - Text: {raw_review['review_text'][:70]}...")
                # In later tasks, this will trigger further processing (e.g., storage, rule engine)
                # For now, just consume and print/log.
            kafka_consumer.commit()
    ```

---

### Task 1.3: Implement error handling and logging for ingestion

*   **Implementation Plan:**
    1.  **Identify Failure Points:** Analyze the ingestion process (fetching, publishing to queue) for potential errors (network issues, API rate limits, data parsing errors, message queue unavailability).
    2.  **Implement Retry Mechanisms:** For transient errors (e.g., network timeout, temporary API unavailability), implement exponential backoff and retry logic.
    3.  **Structured Logging:** Use a structured logging framework (e.g., Python's `logging` module with JSON formatter) to log key events, errors, and warnings. Log details like `review_id`, `product_asin`, error message, timestamp.
    4.  **Dead Letter Queue (DLQ):** For messages that consistently fail processing or cannot be delivered (e.g., malformed data), configure a Dead Letter Queue in the message queuing system to store them for later inspection and reprocessing.
    5.  **Monitoring and Alerts:** Set up basic monitoring for ingestion service health and error rates (e.g., number of messages sent, number of errors, latency).

*   **Data Models and Architecture:**
    *   **Architecture:**
        *   **Ingestion Service:** Enhanced with retry logic and detailed logging.
        *   **Message Queue:** Configured with a DLQ for failed messages.
        *   **Logging System:** Centralized logging (e.g., using a JSON logger that integrates with tools like ELK Stack, Splunk, or cloud-native logging services).
    *   No new specific data models, but log entries become a critical "data type" for operational analysis.

*   **Assumptions and Technical Decisions:**
    *   **Assumption:** A logging framework/system is available (e.g., Python's `logging`, a cloud-based logging service).
    *   **Technical Decision:** Use the `tenacity` library in Python for robust retry mechanisms with exponential backoff.
    *   **Technical Decision:** Define clear policies for retries (max attempts, backoff strategy) and DLQ handling.

*   **Code Snippets/Pseudocode:**
    ```python
    import logging
    import json
    import time
    from datetime import datetime
    from tenacity import retry, stop_after_attempt, wait_exponential, RetryError # Assuming tenacity library

    # Configure structured logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Placeholder for Kafka producer and consumer clients
    class MockKafkaProducer:
        def send(self, topic, value):
            print(f"MOCK KAFKA: Publishing to {topic}: {value.decode()}")
            if "fail_on_publish" in value.decode(): # Simulate a publishing error
                raise ConnectionError("Simulated Kafka connection error")

    class MockAmazonReviewsAPI:
        def fetch_new_reviews(self, since):
            print(f"MOCK API: Fetching reviews since {since}")
            if datetime.now().second % 10 == 0: # Simulate transient API error every 10 seconds
                raise ConnectionError("Simulated API rate limit / transient error")
            return [
                type('obj', (object,), {'id':'R_new1', 'asin':'B00C1', 'reviewer_name':'Alice', 'text':'New great product!', 'title':'Good', 'rating':5, 'date':'2023-11-01T11:00:00Z', 'helpfulness':10}),
                type('obj', (object,), {'id':'R_new2', 'asin':'B00C2', 'reviewer_name':'Bob', 'text':'New bad product.', 'title':'Bad', 'rating':1, 'date':'2023-11-01T11:05:00Z', 'helpfulness':2}),
            ]
    kafka_producer = MockKafkaProducer()
    AmazonReviewsAPI = MockAmazonReviewsAPI()

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_reviews_with_retries(last_timestamp):
        try:
            logger.info(f"Attempting to fetch reviews since {last_timestamp}")
            reviews = AmazonReviewsAPI.fetch_new_reviews(since=last_timestamp)
            logger.info(f"Successfully fetched {len(reviews)} reviews.")
            return reviews
        except Exception as e:
            logger.warning(f"Failed to fetch reviews (will retry): {e}", exc_info=True)
            raise # Re-raise to trigger tenacity retry

    def publish_to_message_queue_with_dlq(topic, data):
        try:
            serialized_data = json.dumps(data).encode('utf-8')
            kafka_producer.send(topic, value=serialized_data)
            logger.info(f"Published review {data.get('review_id')} to {topic}")
        except Exception as e:
            logger.error(f"Failed to publish review {data.get('review_id')} to {topic}. Sending to DLQ.", exc_info=True)
            # In a real system, you'd send to a dedicated DLQ topic or service
            dlq_topic = f"{topic}_dlq"
            kafka_producer.send(dlq_topic, value=json.dumps({"original_data": data, "error": str(e), "timestamp": datetime.utcnow().isoformat()}).encode('utf-8'))


    def ingest_amazon_reviews_robust():
        # Placeholder for state management (e.g., from a database or Redis)
        def get_last_ingested_timestamp_from_db():
            return "2023-11-01T00:00:00Z"
        def update_last_ingested_timestamp_in_db(timestamp):
            print(f"Updated last ingested timestamp to: {timestamp}")

        last_ingested_ts = get_last_ingested_timestamp_from_db()
        try:
            new_reviews = fetch_reviews_with_retries(last_ingested_ts)
            for review in new_reviews:
                raw_review_data = {
                    "review_id": review.id,
                    "product_asin": review.asin,
                    "reviewer_name": review.reviewer_name,
                    "review_text": review.text,
                    "review_title": review.title,
                    "rating": review.rating,
                    "review_date": review.date,
                    "helpfulness_votes": review.helpfulness,
                    "ingestion_timestamp": datetime.utcnow().isoformat()
                }
                publish_to_message_queue_with_dlq("raw_amazon_reviews_topic", raw_review_data)
            if new_reviews:
                update_last_ingested_timestamp_in_db(new_reviews[-1].date)
        except RetryError as e:
            logger.critical(f"Ingestion process failed after multiple retries: {e}", exc_info=True)
        except Exception as e:
            logger.critical(f"Ingestion process failed catastrophically: {e}", exc_info=True)

    # Example of running the ingestion (would be in a loop or scheduled job)
    # if __name__ == "__main__":
    #     ingest_amazon_reviews_robust()
    #     time.sleep(5) # Wait a bit and try again to demonstrate retry/error
    #     ingest_amazon_reviews_robust()
    ```

---

### Task 1.4: Testing and validation of real-time ingestion

*   **Implementation Plan:**
    1.  **Unit Tests:** Write unit tests for individual components of the ingestion service (e.g., `fetch_reviews` function, data parsing logic, message queue publishing utility). Mock external dependencies like API calls or message queue clients.
    2.  **Integration Tests:** Set up a test environment (e.g., local Docker containers for message queue) and perform integration tests to ensure the ingestion service correctly publishes messages to the queue.
    3.  **End-to-End Tests:** Simulate new reviews appearing at the source and verify that they flow through the entire pipeline (ingestion -> message queue -> basic consumer) and are logged/printed as expected. Monitor logs for errors and successful ingestion.
    4.  **Performance Testing (Basic):** Test the ingestion pipeline with a simulated high volume of reviews to assess its capacity, latency, and identify bottlenecks under load.
    5.  **Monitoring Validation:** Verify that error logs and metrics (e.g., messages produced, DLQ messages) are correctly emitted and visible in the monitoring system.

*   **Data Models and Architecture:**
    *   No new data models/architecture are introduced. The focus is on verifying the correctness and robustness of existing components.

*   **Assumptions and Technical Decisions:**
    *   **Assumption:** A testing framework (e.g., `pytest` in Python) is available and used consistently.
    *   **Technical Decision:** Use mocking libraries (e.g., `unittest.mock`) for isolating components during unit testing.
    *   **Technical Decision:** Define clear test data sets for various scenarios (happy path, edge cases, error conditions, malformed data).
    *   **Technical Decision:** For E2E tests, use containerization (e.g., Docker Compose) to spin up isolated test environments including Kafka, source mocks, and the ingestion service.

*   **Code Snippets/Pseudocode:**
    ```python
    import unittest
    from unittest.mock import patch, MagicMock, call
    import json
    from datetime import datetime
    import logging

    # Suppress actual logging during tests if desired, or capture it
    logging.disable(logging.CRITICAL)

    # Assuming 'ingestion_module' contains the functions from Task 1.3
    # For testing, we'd import the actual module
    # from your_project.ingestion import ingest_amazon_reviews_robust, fetch_reviews_with_retries, publish_to_message_queue_with_dlq

    # Mock implementation of review object for testing
    class MockReview:
        def __init__(self, id, asin, reviewer_name, text, title, rating, date, helpfulness):
            self.id = id
            self.asin = asin
            self.reviewer_name = reviewer_name
            self.text = text
            self.title = title
            self.rating = rating
            self.date = date
            self.helpfulness = helpfulness

    class TestIngestionService(unittest.TestCase):

        @patch('__main__.MockAmazonReviewsAPI.fetch_new_reviews') # Patch the actual function being called
        @patch('__main__.MockKafkaProducer.send')
        @patch('__main__.get_last_ingested_timestamp_from_db', return_value="2023-11-01T00:00:00Z")
        @patch('__main__.update_last_ingested_timestamp_in_db')
        def test_ingest_amazon_reviews_success(self, mock_update_ts, mock_get_ts, mock_kafka_send, mock_fetch):
            # Setup mock return values
            mock_fetch.return_value = [
                MockReview(id="R1", asin="B00AAAAAAA", reviewer_name="User1", text="Great product!", title="Good", rating=5, date="2023-11-01T10:00:00Z", helpfulness=10),
                MockReview(id="R2", asin="B00BBBBBBB", reviewer_name="User2", text="Okay product.", title="Neutral", rating=3, date="2023-11-01T10:05:00Z", helpfulness=5),
            ]

            # Call the function under test
            ingest_amazon_reviews_robust()

            # Assertions
            mock_fetch.assert_called_once_with("2023-11-01T00:00:00Z")
            self.assertEqual(mock_kafka_send.call_count, 2) # Two reviews should be sent

            # Verify content of the sent messages (rough check for dynamic parts)
            call_args_list = mock_kafka_send.call_args_list
            sent_data_r1 = json.loads(call_args_list[0].kwargs['value'].decode('utf-8'))
            sent_data_r2 = json.loads(call_args_list[1].kwargs['value'].decode('utf-8'))

            self.assertEqual(sent_data_r1['review_id'], "R1")
            self.assertEqual(sent_data_r2['review_id'], "R2")
            self.assertIn('ingestion_timestamp', sent_data_r1)
            self.assertIn('ingestion_timestamp', sent_data_r2)

            mock_update_ts.assert_called_once_with("2023-11-01T10:05:00Z") # Timestamp of the last review

        @patch('__main__.MockAmazonReviewsAPI.fetch_new_reviews', side_effect=ConnectionError("API Error"))
        @patch('__main__.MockKafkaProducer.send')
        @patch('__main__.get_last_ingested_timestamp_from_db', return_value="2023-11-01T00:00:00Z")
        @patch('__main__.update_last_ingested_timestamp_in_db')
        @patch('logging.critical') # Mock the critical logger call for the retry error
        def test_ingest_amazon_reviews_api_failure_with_retries(self, mock_log_critical, mock_update_ts, mock_get_ts, mock_kafka_send, mock_fetch):
            # The @retry decorator on fetch_reviews_with_retries will cause it to retry 5 times
            # and then raise RetryError, which will be caught by ingest_amazon_reviews_robust
            ingest_amazon_reviews_robust()

            # The fetch function should be called 5 times (initial + 4 retries)
            self.assertEqual(mock_fetch.call_count, 5)
            mock_kafka_send.assert_not_called() # No messages should be sent to Kafka
            mock_update_ts.assert_not_called() # Timestamp should not be updated on failure
            mock_log_critical.assert_called_once()
            self.assertIn("Ingestion process failed after multiple retries", mock_log_critical.call_args[0][0])

        @patch('__main__.MockAmazonReviewsAPI.fetch_new_reviews')
        @patch('__main__.MockKafkaProducer.send', side_effect=ConnectionError("fail_on_publish")) # Simulate Kafka publish error
        @patch('__main__.get_last_ingested_timestamp_from_db', return_value="2023-11-01T00:00:00Z")
        @patch('__main__.update_last_ingested_timestamp_in_db')
        def test_ingest_amazon_reviews_kafka_failure_to_dlq(self, mock_update_ts, mock_get_ts, mock_kafka_send, mock_fetch):
            mock_fetch.return_value = [
                MockReview(id="R1", asin="B00AAAAAAA", reviewer_name="User1", text="Good", title="Good", rating=5, date="2023-11-01T10:00:00Z", helpfulness=10),
            ]

            ingest_amazon_reviews_robust()

            # Two calls to kafka_send: one for the original topic (which fails), one for the DLQ
            self.assertEqual(mock_kafka_send.call_count, 2)
            # Verify the DLQ call
            dlq_call = mock_kafka_send.call_args_list[1]
            self.assertEqual(dlq_call.args[0], "raw_amazon_reviews_topic_dlq")
            dlq_data = json.loads(dlq_call.kwargs['value'].decode('utf-8'))
            self.assertEqual(dlq_data['original_data']['review_id'], "R1")
            self.assertIn("Simulated Kafka connection error", dlq_data['error'])
            mock_update_ts.assert_called_once() # Timestamp should still update if review was fetched

    # Pseudocode for a basic end-to-end test script
    def run_e2e_ingestion_test():
        print("--- Starting End-to-End Ingestion Test ---")
        # In a real scenario, this would orchestrate Docker containers or cloud resources.

        # 1. Start (or ensure running) mocked Kafka and Ingestion Service.
        #    For this example, we'll directly call the ingestion function and mock consumer.
        # 2. Simulate new reviews at the source (e.g., by ensuring MockAmazonReviewsAPI returns data).
        # 3. Trigger the ingestion process.
        ingest_amazon_reviews_robust()
        print("Ingestion service triggered.")

        # 4. Simulate the consumer reading from the topic
        class MockKafkaConsumerMessage:
            def __init__(self, value):
                self.value = value
        
        class MockKafkaConsumer:
            def __init__(self, messages_to_return):
                self._messages = messages_to_return
                self._index = 0
            
            def subscribe(self, topics):
                print(f"MOCK KAFKA CONSUMER: Subscribed to {topics}")
            
            def __iter__(self):
                return self
            
            def __next__(self):
                if self._index < len(self._messages):
                    msg = self._messages[self._index]
                    self._index += 1
                    return msg
                raise StopIteration
            
            def commit(self):
                print("MOCK KAFKA CONSUMER: Committed offset.")

        # Simulate messages that would have been produced by the ingestion
        mock_raw_review_1 = {
            "review_id": "R1", "product_asin": "B00AAAAAAA", "reviewer_name": "User1",
            "review_text": "Great product!", "review_title": "Good", "rating": 5,
            "review_date": "2023-11-01T10:00:00Z", "helpfulness_votes": 10,
            "ingestion_timestamp": datetime.utcnow().isoformat()
        }
        mock_raw_review_2 = {
            "review_id": "R2", "product_asin": "B00BBBBBBB", "reviewer_name": "User2",
            "review_text": "Okay product.", "review_title": "Neutral", "rating": 3,
            "review_date": "2023-11-01T10:05:00Z", "helpfulness_votes": 5,
            "ingestion_timestamp": datetime.utcnow().isoformat()
        }

        mock_consumer_messages = [
            MockKafkaConsumerMessage(json.dumps(mock_raw_review_1).encode('utf-8')),
            MockKafkaConsumerMessage(json.dumps(mock_raw_review_2).encode('utf-8')),
        ]

        # Use the mocked consumer to simulate processing
        original_kafka_consumer = globals().get('kafka_consumer_instance', None) # Store actual if exists
        globals()['kafka_consumer_instance'] = MockKafkaConsumer(mock_consumer_messages)
        
        print("\n--- Simulating Consumer Processing ---")
        # Re-using the process_raw_reviews_consumer from Task 1.2's pseudocode.
        # This would usually run in a separate service.
        def process_mocked_raw_reviews():
            # In a real system, kafka_consumer_instance would be instantiated once
            consumer = globals()['kafka_consumer_instance']
            consumer.subscribe(["raw_amazon_reviews_topic"])
            try:
                for message in consumer:
                    raw_review = json.loads(message.value.decode('utf-8'))
                    print(f"E2E CONSUMER: Received raw review (ID: {raw_review['review_id']}) - Text: {raw_review['review_text'][:70]}...")
                consumer.commit()
            except StopIteration:
                pass # Expected when mock consumer runs out of messages

        process_mocked_raw_reviews()

        # 5. Verify logs for successful ingestion and consumer processing.
        # This would typically involve checking a centralized log system.
        print("\n--- Verifying Logs (Conceptual) ---")
        print("Check ingestion service logs for 'Successfully fetched X reviews' and 'Published review Y'.")
        print("Check consumer service logs for 'Received raw review (ID: Z)'.")
        print("Check for any error/critical logs.")

        print("--- End-to-End test passed conceptually ---")

    # Example of running unit tests (e.g., with unittest.main())
    # if __name__ == '__main__':
    #     unittest.main(argv=['first-arg-is-ignored'], exit=False)
    #     run_e2e_ingestion_test()
    ```
