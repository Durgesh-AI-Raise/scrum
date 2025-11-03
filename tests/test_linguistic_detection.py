import unittest
from src.linguistic_detection import LinguisticDetector

class TestLinguisticDetector(unittest.TestCase):
    def setUp(self):
        self.detector = LinguisticDetector(keyword_stuffing_threshold=3, sentiment_threshold=0.7)

    def test_keyword_stuffing_detection(self):
        # Test case 1: Keyword stuffing detected
        text1 = "This product is absolutely amazing! I love it, love it, love it! Highly recommend it to everyone."
        is_ks1, confidence1 = self.detector.detect_keyword_stuffing(text1)
        self.assertTrue(is_ks1)
        self.assertGreater(confidence1, 0.0)

        # Test case 2: Keyword stuffing not detected
        text2 = "A decent product, performs as expected. Very good experience."
        is_ks2, confidence2 = self.detector.detect_keyword_stuffing(text2)
        self.assertFalse(is_ks2)
        self.assertEqual(confidence2, 0.0)

        # Test case 3: Empty text
        text3 = ""
        is_ks3, confidence3 = self.detector.detect_keyword_stuffing(text3)
        self.assertFalse(is_ks3)
        self.assertEqual(confidence3, 0.0)

        # Test case 4: Keyword stuffing with common words (should be ignored)
        text4 = "the the the product is good"
        is_ks4, confidence4 = self.detector.detect_keyword_stuffing(text4)
        self.assertFalse(is_ks4)
        self.assertEqual(confidence4, 0.0)

    def test_extreme_sentiment_detection(self):
        # Test case 1: Extreme positive sentiment
        text1 = "Amazing! Fantastic! Superb! Excellent! Top-notch! A+++ This is the best product ever."
        is_es1, confidence1 = self.detector.detect_extreme_sentiment(text1)
        self.assertTrue(is_es1)
        self.assertGreater(confidence1, 0.7) # Should be high positive score

        # Test case 2: Extreme negative sentiment
        text2 = "I am utterly disappointed with this product. It broke immediately and was a complete letdown. Worst product."
        is_es2, confidence2 = self.detector.detect_extreme_sentiment(text2)
        self.assertTrue(is_es2)
        self.assertGreater(confidence2, 0.7) # Should be high absolute negative score

        # Test case 3: Neutral sentiment
        text3 = "It's okay. Nothing special. Just a product."
        is_es3, confidence3 = self.detector.detect_extreme_sentiment(text3)
        self.assertFalse(is_es3)
        self.assertEqual(confidence3, 0.0)

        # Test case 4: Mixed sentiment, not extreme
        text4 = "This product has some good features, but also some drawbacks. It's alright."
        is_es4, confidence4 = self.detector.detect_extreme_sentiment(text4)
        self.assertFalse(is_es4)
        self.assertEqual(confidence4, 0.0)

        # Test case 5: Empty text
        text5 = ""
        is_es5, confidence5 = self.detector.detect_extreme_sentiment(text5)
        self.assertFalse(is_es5)
        self.assertEqual(confidence5, 0.0)

if __name__ == '__main__':
    unittest.main()