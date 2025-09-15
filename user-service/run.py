<<<<<<< HEAD
# chạy: python run.py
from app import create_app
=======
from app import create_app
from app.config.settings import Config
>>>>>>> clean-branch

app = create_app()

if __name__ == "__main__":
<<<<<<< HEAD
    app.run(host="0.0.0.0", port=5002, debug=True)
=======
    app.run(host="0.0.0.0", port=Config.USER_SERVICE_PORT, debug=True)
>>>>>>> clean-branch
