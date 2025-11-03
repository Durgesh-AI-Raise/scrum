import json
import os
import boto3
import base64
import re # For simple regex based keyword spotting
from datetime import datetime

# Environment variables for configuration
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "ARIS_FlaggedReviews")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

comprehend_client = boto3.client("comprehend")

# Keyword lists for initial content moderation rules (can be externalized to config)
SPAM_KEYWORDS = [
    r"\bfree\s+money\b", r"\bget\s+rich\s+quick\b", r"\bbuy\s+now\b", r"\bdiscount\s+code\b",
    r"\bclick\s+here\b", r"\bcoupon\s+code\b", r"\bwin\s+prize\b", r"\bdeal\s+of\s+the\s+day\b",
    r"\bloan\s+offer\b", r"\binvestment\s+opportunity\b"
]
HATE_SPEECH_KEYWORDS = [ # Highly simplified and example-based, needs careful and continuous tuning
    r"\bkiller\b", r"\bhate\b", r"\battack\b", r"\b[racial_slur]\b", r"\b[gender_slur]\b",
    r"\bidiot\b", r"\bstupid\b", r"\bdisgusting\b", r"\bfreak\b" # Context is crucial for these
]
ILLEGAL_KEYWORDS = [
    r"\bdrugs\b", r"\bweapon\b", r"\bfirearm\b", r"\billegal\b", r"\bbomb\b", r"\bexploit\b",
    r"\bchild\s+abuse\b"
]
IRRELEVANT_TEXT_THRESHOLD = 10 # Minimum word count for relevant reviews

def contains_keywords_regex(text, keywords_list):
    """Checks if text contains any of the keywords using regex."""
    text_lower = text.lower()
    for keyword_pattern in keywords_list:
        if re.search(keyword_pattern, text_lower):
            return True
    return False

def lambda_handler(event, context):
    """
    Processes Kinesis records for content moderation issues (spam, irrelevant, hate speech, illegal).
    """
    flagged_items = []
    
    for record in event["Records"]:
        try:
            payload = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            review = json.loads(payload)

            review_id = review.get("review_id")
            product_id = review.get("product_id")
            user_id = review.get("user_id")
            review_text = review.get("review_text", "")
            
            flagged = False
            detection_rules = []

            # --- Rule 1: Spam Keywords ---
            if contains_keywords_regex(review_text, SPAM_KEYWORDS):
                flagged = True
                detection_rules.append("Rule: Contains Spam Keywords")
            
            # --- Rule 2: Hate Speech / Toxicity (via Keywords & Comprehend Sentiment) ---
            # Initial approach: Combine keyword spotting with sentiment analysis for basic detection
            comprehend_language = "en" # Default to English
            try:
                # Detect dominant language for better sentiment analysis accuracy
                language_response = comprehend_client.detect_dominant_language(Text=review_text)
                if language_response and language_response["Languages"]:
                    comprehend_language = language_response["Languages"][0]["LanguageCode"]
            except Exception as e:
                print(f"Warning: Error detecting language for review {review_id}: {e}")
                # Continue with default language if language detection fails

            if contains_keywords_regex(review_text, HATE_SPEECH_KEYWORDS):
                if not flagged: # Avoid re-adding if already flagged
                    flagged = True
                detection_rules.append("Rule: Contains Hate Speech Keywords (via Keyword Spotting)")
            
            try:
                # Perform sentiment analysis
                sentiment_response = comprehend_client.detect_sentiment(Text=review_text, LanguageCode=comprehend_language)
                sentiment = sentiment_response["Sentiment"]
                sentiment_score = sentiment_response["SentimentScore"]
                
                # If sentiment is overwhelmingly negative and matches certain patterns, it could indicate abuse
                # This is a very basic heuristic; a full hate speech detector would be more sophisticated.
                if sentiment == "NEGATIVE" and sentiment_score["Negative"] > 0.9: # Very high confidence of negativity
                    if not flagged:
                        flagged = True
                    detection_rules.append(f"Rule: Extremely Negative Sentiment ({sentiment_score['Negative']:.2f} confidence)")

            except Exception as e:
                print(f"Warning: Error detecting sentiment for review {review_id}: {e}")
                
            # --- Rule 3: Illegal Content Keywords ---
            if contains_keywords_regex(review_text, ILLEGAL_KEYWORDS):
                if not flagged:
                    flagged = True
                detection_rules.append("Rule: Contains Illegal Content Keywords")
            
            # --- Rule 4: Irrelevant/Gibberish Content ---
            # Very short reviews with little to no meaningful words, or just random characters
            word_count = len(review_text.split())
            if word_count < IRRELEVANT_TEXT_THRESHOLD and not re.search(r'\w{2,}', review_text): # Less than X words and few meaningful words
                if not flagged:
                    flagged = True
                detection_rules.append("Rule: Very short and potentially irrelevant/gibberish content")
            
            if flagged:
                flag_timestamp = datetime.utcnow().isoformat() + "Z"
                flag_id = f"CM_{review_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

                flagged_item = {
                    "flag_id": flag_id,
                    "review_id": review_id,
                    "product_id": product_id,
                    "user_id": user_id,
                    "review_text": review_text,
                    "flag_type": "ContentModeration",
                    "detection_rule": "; ".join(detection_rules),
                    "flag_timestamp": flag_timestamp,
                    "status": "PENDING_REVIEW",
                    "metadata": {
                        "review_length_words": word_count,
                        "sentiment": sentiment if 'sentiment' in locals() else 'N/A',
                        "sentiment_score_negative": sentiment_score["Negative"] if 'sentiment_score' in locals() else 0.0,
                    }
                }
                flagged_items.append(flagged_item)

        except Exception as e:
            print(f"Error processing Kinesis record: {e}. Record: {record}")
    
    if flagged_items:
        with table.batch_writer() as batch:
            for item in flagged_items:
                batch.put_item(Item=item)
        print(f"Successfully flagged {len(flagged_items)} reviews for content moderation issues.")
    
    return {
        "statusCode": 200,
        "body": json.dumps(f"Processed {len(event['Records'])} Kinesis records. Flagged {len(flagged_items)} reviews.")
    }
