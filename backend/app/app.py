# backend/app/config.py
import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost/reviews_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MOCK_REVIEW_DATA_PATH = os.environ.get('MOCK_REVIEW_DATA_PATH', 'mock_amazon_reviews.json')
    # Add other configuration variables here (e.g., API keys, external service URLs)

# backend/app/app.py
from flask import Flask
from flask_cors import CORS
from .models import db
from .routes import flagged_reviews_bp # Import the blueprint
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app) # Enable CORS for all origins and routes, or configure specifically

    # Register blueprints
    app.register_blueprint(flagged_reviews_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Only for development: create database tables if they don't exist
        # In production, use database migrations (e.g., Flask-Migrate)
        db.create_all()
    app.run(debug=True, port=5000)
