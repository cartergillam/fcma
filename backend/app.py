import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Secure configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

# Initialize extensions
mongo = PyMongo(app)
jwt = JWTManager(app)

@app.route("/")
def home():
    return jsonify(message="FCMA Backend is running securely!")

if __name__ == "__main__":
    app.run(debug=True)
