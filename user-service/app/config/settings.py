import os
from dotenv import load_dotenv

# Load environment variables from .env file
try:
    load_dotenv(dotenv_path='.env')
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")

class Config:
    """Cấu hình ứng dụng user-service"""
    
    # Firebase
    FIREBASE_PROJECT_ID = 'algodumb-22983'
    GOOGLE_APPLICATION_CREDENTIALS = 'algodumb-22983-firebase-adminsdk-fbsvc-c5d08813da.json'
    
    # Services
    FACEID_SERVICE_URL = os.getenv('FACEID_SERVICE_URL', 'http://localhost:5000')
    USER_SERVICE_PORT = int(os.getenv('USER_SERVICE_PORT', 5002))
    
    # Performance - Yêu cầu ≤ 2s cho 1 ảnh
    MATCH_THRESHOLD = float(os.getenv('MATCH_THRESHOLD', '0.6'))
    MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', '2097152'))  # 2MB (giảm để xử lý nhanh hơn)
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '2000'))   # 2s
    FACEID_TIMEOUT = int(os.getenv('FACEID_TIMEOUT', '1500'))     # 1.5s (để dành 0.5s cho xử lý khác)
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
