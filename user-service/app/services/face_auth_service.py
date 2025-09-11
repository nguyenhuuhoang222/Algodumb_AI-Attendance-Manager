# Gọi faceid-service qua HTTP
import requests
import json
from typing import List

class FaceAuthService:
    # Service gọi faceid-service để xử lý nhận dạng khuôn mặt 

    def __init__(self, base_url: str):
        # 1. Khởi tạo base URL cho faceid-service
        self.base_url = base_url.rstrip("/")

    def encode(self, image_bytes: bytes) -> List[float]:
        # Gọi faceid-service để encode khuôn mặt
        # 2. Chuẩn bị file upload
        files = {"file": ("face.jpg", image_bytes, "image/jpeg")}
        # 3. Gọi API encode-face
        r = requests.post(f"{self.base_url}/encode-face", files=files, timeout=20)
        r.raise_for_status()
        # 4. Trả về embedding vector
        return r.json().get("embedding", [])

    def compare(self, emb1, emb2):
        # Gọi faceid-service để so sánh 2 embedding
        # 5. Chuẩn bị payload
        payload = {"emb1": emb1, "emb2": emb2}
        # 6. Gọi API compare-faces
        r = requests.post(f"{self.base_url}/compare-faces", json=payload, timeout=20)
        r.raise_for_status()
        # 7. Trả về kết quả so sánh
        return r.json()
