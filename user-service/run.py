from app import create_app
from app.config.settings import Config

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.USER_SERVICE_PORT, debug=True)
