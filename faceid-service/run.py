# chạy: python run.py
from api import create_app

app = create_app()

if __name__ == "__main__":
    # Debug chỉ dùng môi trường dev
    app.run(host="0.0.0.0", port=5001, debug=True)
