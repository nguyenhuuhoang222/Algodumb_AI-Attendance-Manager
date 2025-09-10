from flask import Flask
from flask_cors import CORS
from .face_api import face_bp

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(face_bp, url_prefix="/api")
    return app
