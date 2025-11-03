
# heuristic_engine_service.py
import json
import logging
from abc import ABC, abstractmethod
import psycopg2 # For DB interaction
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'amazon_reviews'),
        user=os.getenv('DB_USER', 'user'),
        password=os.getenv('DB_PASSWORD', 'password')
    )

class HeuristicRule(ABC):
    """Abstract base class for all heuristic rules."""
    def __init__(self, rule_id: str, name: str, config: dict, severity: str):
        self.rule_id = rule_id
        self.name = name
        self.config = config
        self.severity = severity
        self.db_conn_provider = None # Will be set by HeuristicEngine

    def set_db_connection_provider(self, provider_func):
        self.db_conn_provider = provider_func

    @abstractmethod
    def evaluate(self, review_data: dict) -> tuple[bool, str]:
        """
        Evaluates the rule against the review data.
        Returns (is_flagged, reason_message)
        """
        pass

class HeuristicEngine:
    """Manages and executes heuristic rules."""
    def __init__(self, db_config: dict):
        self.rules: list[HeuristicRule] = []
        self.db_config = db_config
        self._load_rules_from_db()

    def _get_db_connection(self):
        return psycopg2.connect(**self.db_config)

    def _load_rules_from_db(self):
        conn = None
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT rule_id, rule_name, rule_config, severity, rule_type FROM heuristic_rules WHERE is_active = TRUE")
            active_rules = cur.fetchall()
            cur.close()

            self.rules = []
            for rule_id, rule_name, rule_config, severity, rule_type in active_rules:
                # Dynamically create rule instances based on rule_type
                rule_instance = None
                if rule_type == 'duplicate_content':
                    rule_instance = DuplicateContentRule(rule_id, rule_name, rule_config or {}, severity)
                elif rule_type == 'blocked_ip':
                    rule_instance = BlockedIPRule(rule_id, rule_name, rule_config or {}, severity)
                elif rule_type == 'keyword_excess':
                    rule_instance = ExcessiveKeywordsRule(rule_id, rule_name, rule_config or {}, severity)
                # Add other rule types here

                if rule_instance:
                    rule_instance.set_db_connection_provider(self._get_db_connection)
                    self.rules.append(rule_instance)
                    logger.info(f"Loaded rule: {rule_name} ({rule_type})")
                else:
                    logger.warning(f"Unknown rule type: {rule_type} for rule {rule_name}")

        except Exception as e:
            logger.error(f"Error loading heuristic rules from DB: {e}")
        finally:
            if conn: conn.close()
        logger.info(f"Loaded {len(self.rules)} active heuristic rules.")


    def process_review(self, review_data: dict):
        flags = []
        review_id = review_data.get('review_id')
        if not review_id:
            logger.error("Review data missing 'review_id'. Skipping processing.")
            return

        for rule in self.rules:
            try:
                is_flagged, reason = rule.evaluate(review_data)
                if is_flagged:
                    flags.append({
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "reason": reason,
                        "severity": rule.severity,
                        "flag_type": rule.name.lower().replace(" ", "_") # Infer type from name
                    })
            except Exception as e:
                logger.error(f"Error evaluating rule '{rule.name}' for review {review_id}: {e}")
        
        if flags:
            logger.warning(f"Review {review_id} flagged by rules: {flags}")
            self._update_review_status(review_id, flags)
        else:
            logger.info(f"Review {review_id} passed all heuristic checks.")

    def _update_review_status(self, review_id: str, flags: list[dict]):
        """Updates the review's flagging status in the database."""
        conn = None
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            # Combine reasons, find highest severity, and unique flag types
            flag_reasons = "; ".join([f["rule_name"] + ": " + f["reason"] for f in flags])
            
            severity_order = ["low", "medium", "high", "critical"]
            highest_severity = "low"
            for f in flags:
                if severity_order.index(f["severity"].lower()) > severity_order.index(highest_severity.lower()):
                    highest_severity = f["severity"]

            flag_types = ", ".join(list(set([f["flag_type"] for f in flags])))

            cur.execute(
                """
                UPDATE reviews
                SET is_flagged = TRUE,
                    flag_reason = COALESCE(flag_reason || '; ', '') || %s,
                    flag_severity = %s,
                    flag_type = COALESCE(flag_type || ',', '') || %s,
                    status = 'pending_review'
                WHERE review_id = %s
                RETURNING *;
                """,
                (flag_reasons, highest_severity, flag_types, review_id)
            )
            conn.commit()
            logger.info(f"Updated review {review_id} with flags: {flags}")
        except psycopg2.Error as db_err:
            logger.error(f"DB Error updating review {review_id} with flags: {db_err}")
            if conn: conn.rollback()
        except Exception as e:
            logger.error(f"Error updating review {review_id} with flags: {e}")
        finally:
            if conn: conn.close()

# Dummy rule implementations (will be fully fleshed out in subsequent tasks)
class DuplicateContentRule(HeuristicRule):
    def evaluate(self, review_data: dict) -> tuple[bool, str]:
        # Placeholder for actual logic (see Task 2.2)
        # logger.debug(f"Evaluating DuplicateContentRule for {review_data.get('review_id')}")
        return False, ""

class BlockedIPRule(HeuristicRule):
    def evaluate(self, review_data: dict) -> tuple[bool, str]:
        # Placeholder for actual logic (see Task 2.3)
        # logger.debug(f"Evaluating BlockedIPRule for {review_data.get('review_id')}")
        return False, ""

class ExcessiveKeywordsRule(HeuristicRule):
    def evaluate(self, review_data: dict) -> tuple[bool, str]:
        # Placeholder for actual logic (see Task 2.4)
        # logger.debug(f"Evaluating ExcessiveKeywordsRule for {review_data.get('review_id')}")
        return False, ""

# Example usage:
# if __name__ == "__main__":
#     # Ensure DB is set up and heuristic_rules table has some entries
#     # INSERT INTO heuristic_rules (rule_id, rule_name, rule_description, rule_type, is_active, severity)
#     # VALUES ('rule-1', 'Duplicate Content Check', 'Flags reviews with identical content', 'duplicate_content', TRUE, 'high');
#     # INSERT INTO heuristic_rules (rule_id, rule_name, rule_description, rule_type, is_active, severity)
#     # VALUES ('rule-2', 'Blocked IP Check', 'Flags reviews from known blocked IPs', 'blocked_ip', TRUE, 'critical');
#     # INSERT INTO heuristic_rules (rule_id, rule_name, rule_description, rule_type, rule_config, is_active, severity)
#     # VALUES ('rule-3', 'Excessive Keywords Check', 'Flags reviews with many suspicious keywords', 'keyword_excess', '{"threshold": 3}', TRUE, 'medium');

#     db_conf = {'host': 'localhost', 'database': 'amazon_reviews', 'user': 'user', 'password': 'password'}
#     engine = HeuristicEngine(db_conf)
#     
#     sample_review = {
#         'review_id': 'test_review_123',
#         'product_id': 'prod_abc',
#         'user_id': 'user_xyz',
#         'comment': 'This is a test review about a product. It is good.',
#         'source_ip': '192.168.0.1'
#     }
#     engine.process_review(sample_review)
