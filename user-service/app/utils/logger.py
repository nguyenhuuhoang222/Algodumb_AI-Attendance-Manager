import logging
import json
from datetime import datetime
from typing import Dict, Any

class StructuredLogger:
    # Logger có cấu trúc cho user-service

    def __init__(self, name: str = "user-service"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Tạo formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Tạo handler
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_request(self, method: str, endpoint: str, user_id: str = None, **kwargs):
        # Log HTTP request
        log_data = {
            "type": "request",
            "method": method,
            "endpoint": endpoint,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.info(json.dumps(log_data))
    
    def log_response(self, status_code: int, response_time: float, **kwargs):
        # Log HTTP response
        log_data = {
            "type": "response",
            "status_code": status_code,
            "response_time_ms": response_time,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.info(json.dumps(log_data))
    
    def log_face_recognition(self, action: str, user_id: str = None, similarity: float = None, **kwargs):
        # Log hoạt động nhận dạng khuôn mặt
        log_data = {
            "type": "face_recognition",
            "action": action,
            "user_id": user_id,
            "similarity": similarity,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.info(json.dumps(log_data))
    
    def log_error(self, error: str, user_id: str = None, **kwargs):
        # Log lỗi
        log_data = {
            "type": "error",
            "error": error,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.error(json.dumps(log_data))

# Tạo instance global
logger = StructuredLogger()
