from flask import Flask
from flask_cors import CORS
from .controllers.auth_controller import auth_bp

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(auth_bp, url_prefix="/api")
    return app
