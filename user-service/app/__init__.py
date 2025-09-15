from flask import Flask
from flask_cors import CORS
from .controllers.auth_controller import auth_bp
<<<<<<< HEAD
=======
from .controllers.attendance_controller import attendance_bp
>>>>>>> clean-branch

def create_app():
    app = Flask(__name__)
    CORS(app)
<<<<<<< HEAD
    app.register_blueprint(auth_bp, url_prefix="/api")
=======
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(attendance_bp, url_prefix="/api")
    
    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "healthy", "service": "User Service"}
    
>>>>>>> clean-branch
    return app
