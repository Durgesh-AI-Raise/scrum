from flask import Flask, jsonify
from auth_routes import auth_bp
from user_routes import user_bp
import os

app = Flask(__name__)
# A secret key for Flask sessions and other security purposes. 
# Should be a strong, unique value in production.
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "another-super-secret-key-replace-in-prod") 

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')

@app.route('/')
def health_check():
    return jsonify({"status": "Backend is running!"})

if __name__ == '__main__':
    # When running locally, set FLASK_ENV=development and debug=True
    # In production, debug should be False.
    app.run(debug=True, port=5000)