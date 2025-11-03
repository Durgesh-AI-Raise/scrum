import pickle
import re
import string
import os

# Using scikit-learn for ML components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

class MLReviewDetector:
    def __init__(self, model_path='ml_model.pkl', vectorizer_path='tfidf_vectorizer.pkl'):
        self.model = None
        self.vectorizer = None
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self._load_ml_components()

    def _load_ml_components(self):
        """Loads the pre-trained ML model and TF-IDF vectorizer."""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print(f"ML model loaded from {self.model_path}")
            else:
                print(f"Warning: ML model file not found at {self.model_path}. Please train the model first.")

            if os.path.exists(self.vectorizer_path):
                with open(self.vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                print(f"TF-IDF vectorizer loaded from {self.vectorizer_path}")
            else:
                print(f"Warning: TF-IDF vectorizer file not found at {self.vectorizer_path}. Please train the model first.")

        except Exception as e:
            print(f"Error loading ML components: {e}")
            self.model = None
            self.vectorizer = None

    def _preprocess_text(self, text):
        """Basic text preprocessing for ML model input."""
        if not text: # Handle None or empty string input gracefully
            return ""
        text = str(text).lower() # Ensure text is string and lowercase
        text = re.sub(f"[{re.escape(string.punctuation)}\d]", "", text) # Remove punctuation and digits
        text = re.sub(r'\s+', ' ', text).strip() # Remove extra spaces and strip leading/trailing whitespace
        return text

    def predict_suspicion(self, review_text):
        """Predicts a suspicion score for a given review text (0 to 1)."""
        if not self.model or not self.vectorizer:
            print("ML model or vectorizer not loaded. Returning default score.")
            return 0.5 # Neutral score if model not available

        processed_text = self._preprocess_text(review_text)
        if not processed_text:
            return 0.5 # Neutral score if text is empty after preprocessing

        try:
            # The vectorizer expects an iterable, so wrap the processed text in a list
            text_vector = self.vectorizer.transform([processed_text])

            # Predict probability for the 'suspicious' class (label 1)
            # predict_proba returns [[prob_class_0, prob_class_1]]
            suspicion_score = self.model.predict_proba(text_vector)[0][1]
            return float(suspicion_score)
        except Exception as e:
            print(f"Error during ML prediction: {e}. Returning default score.")
            return 0.5 # Default score on prediction error

# This block demonstrates how to train a mock model and use the detector
# In a real application, model training would be a separate pipeline.
if __name__ == "__main__":
    print("--- ML Review Detector Demo ---")

    # 1. Generate a mock dataset for training
    from sklearn.model_selection import train_test_split
    import pandas as pd

    def generate_ml_dataset(num_normal=100, num_suspicious=20):
        data = []
        labels = []
        # Generate normal reviews
        for i in range(num_normal):
            data.append(f"This is a genuine review about product A. It's really good. Customer satisfaction is high. {i}")
            labels.append(0) # 0 for normal
        # Generate suspicious reviews (e.g., with spammy phrases, unusual structure)
        for i in range(num_suspicious):
            data.append(f"BUY NOW! This amazing product will change your life! LIMITED TIME OFFER. FREE MONEY! act fast! {i}")
            labels.append(1) # 1 for suspicious
        return pd.DataFrame({'text': data, 'label': labels})

    df = generate_ml_dataset()

    X_train, X_test, y_train, y_test = train_test_split(df['text'], df['label'], test_size=0.2, random_state=42)

    # 2. Feature Extraction and Model Training
    print("\nTraining mock ML model...")
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(random_state=42, solver='liblinear') # 'liblinear' for small datasets
    model.fit(X_train_vec, y_train)

    # 3. Save model and vectorizer
    model_filename = 'ml_model.pkl'
    vectorizer_filename = 'tfidf_vectorizer.pkl'
    with open(model_filename, 'wb') as f:
        pickle.dump(model, f)
    with open(vectorizer_filename, 'wb') as f:
        pickle.dump(vectorizer, f)
    print(f"Mock ML model saved to {model_filename}")
    print(f"Mock TF-IDF vectorizer saved to {vectorizer_filename}")

    # 4. Use the detector service to predict suspicion scores
    print("\nUsing MLReviewDetector for inference...")
    detector = MLReviewDetector(model_path=model_filename, vectorizer_path=vectorizer_filename)

    sample_review_1 = "This product is absolutely wonderful, highly recommend!"
    sample_review_2 = "BUY NOW AND GET RICH QUICK! Limited time offer, don't miss out!"
    sample_review_3 = "A decent item for the price, no complaints."
    sample_review_4 = "free money casino!"
    sample_review_5 = None
    sample_review_6 = ""

    print(f"'{sample_review_1}' -> Suspicion Score: {detector.predict_suspicion(sample_review_1):.4f}")
    print(f"'{sample_review_2}' -> Suspicion Score: {detector.predict_suspicion(sample_review_2):.4f}")
    print(f"'{sample_review_3}' -> Suspicion Score: {detector.predict_suspicion(sample_review_3):.4f}")
    print(f"'{sample_review_4}' -> Suspicion Score: {detector.predict_suspicion(sample_review_4):.4f}")
    print(f"'None' -> Suspicion Score: {detector.predict_suspicion(sample_review_5):.4f}")
    print(f"'' -> Suspicion Score: {detector.predict_suspicion(sample_review_6):.4f}")

    # Clean up mock files
    if os.path.exists(model_filename):
        os.remove(model_filename)
    if os.path.exists(vectorizer_filename):
        os.remove(vectorizer_filename)
    print("\nCleaned up mock model files.")

    print("--- Demo Complete ---")
