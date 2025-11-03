
import unittest
from datetime import datetime
from io import StringIO
from unittest.mock import patch

from aris.data_models.review_data import ReviewData
from aris.rule_engine.rules.ip_match_rule import IpMatchRule
from aris.rule_engine.rules.keyword_match_rule import KeywordMatchRule
from aris.rule_engine.rules.rapid_review_rule import RapidReviewRule

class TestRules(unittest.TestCase):

    def setUp(self):
        self.sample_review_data = ReviewData(
            review_id="rev123",
            user_id="user456",
            product_id="prod789",
            ip_address="192.168.1.100",
            text="This is a great product!",
            timestamp=datetime.now()
        )

    def test_ip_match_rule_positive(self):
        rule_definition = {"ips": ["192.168.1.100", "10.0.0.5"]}
        ip_rule = IpMatchRule(id="ip-rule-1", name="Suspicious IP", definition=rule_definition)
        self.assertTrue(ip_rule.evaluate(self.sample_review_data))

    def test_ip_match_rule_negative(self):
        rule_definition = {"ips": ["1.1.1.1", "2.2.2.2"]}
        ip_rule = IpMatchRule(id="ip-rule-2", name="Suspicious IP", definition=rule_definition)
        self.assertFalse(ip_rule.evaluate(self.sample_review_data))

    def test_ip_match_rule_disabled(self):
        rule_definition = {"ips": ["192.168.1.100"]}
        ip_rule = IpMatchRule(id="ip-rule-3", name="Suspicious IP", definition=rule_definition, is_enabled=False)
        self.assertFalse(ip_rule.evaluate(self.sample_review_data))

    def test_keyword_match_rule_any_positive(self):
        rule_definition = {"keywords": ["great", "terrible"], "match_any": True}
        keyword_rule = KeywordMatchRule(id="kw-rule-1", name="Positive Keyword", definition=rule_definition)
        self.assertTrue(keyword_rule.evaluate(self.sample_review_data))

    def test_keyword_match_rule_any_negative(self):
        rule_definition = {"keywords": ["awful", "bad"], "match_any": True}
        keyword_rule = KeywordMatchRule(id="kw-rule-2", name="Negative Keyword", definition=rule_definition)
        self.assertFalse(keyword_rule.evaluate(self.sample_review_data))

    def test_keyword_match_rule_all_positive(self):
        rule_definition = {"keywords": ["great", "product"], "match_any": False}
        keyword_rule = KeywordMatchRule(id="kw-rule-3", name="All Keywords", definition=rule_definition)
        self.assertTrue(keyword_rule.evaluate(self.sample_review_data))

    def test_keyword_match_rule_all_negative(self):
        rule_definition = {"keywords": ["great", "awful"], "match_any": False}
        keyword_rule = KeywordMatchRule(id="kw-rule-4", name="All Keywords Fail", definition=rule_definition)
        self.assertFalse(keyword_rule.evaluate(self.sample_review_data))

    def test_keyword_match_rule_case_insensitivity(self):
        rule_definition = {"keywords": ["PRODUCT"], "match_any": True}
        keyword_rule = KeywordMatchRule(id="kw-rule-5", name="Case Insensitive", definition=rule_definition)
        self.assertTrue(keyword_rule.evaluate(self.sample_review_data))

    def test_keyword_match_rule_disabled(self):
        rule_definition = {"keywords": ["great"], "match_any": True}
        keyword_rule = KeywordMatchRule(id="kw-rule-6", name="Disabled Keyword", definition=rule_definition, is_enabled=False)
        self.assertFalse(keyword_rule.evaluate(self.sample_review_data))

    def test_rapid_review_rule_placeholder_behavior(self):
        rule_definition = {"max_reviews": 5, "time_window_minutes": 60, "group_by": "user_id"}
        rapid_rule = RapidReviewRule(id="rr-rule-1", name="Rapid Review", definition=rule_definition)

        # Use patch to capture stdout
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.assertFalse(rapid_rule.evaluate(self.sample_review_data))
            self.assertIn("INFO: RapidReviewRule 'Rapid Review' (ID: rr-rule-1) is a placeholder and requires external service integration. Not evaluating.", fake_out.getvalue())

# This allows running the tests directly from the file
if __name__ == '__main__':
    unittest.main()
