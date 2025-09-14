# Gọi faceid-service qua HTTP
import requests
import json
from typing import List

class FaceAuthService:
    # Service gọi faceid-service để xử lý nhận dạng khuôn mặt 

    def __init__(self, base_url: str):
        # 1. Khởi tạo base URL cho faceid-service
        self.base_url = base_url.rstrip("/")

<<<<<<< HEAD
    def encode(self, image_bytes: bytes) -> str:
        files = {"image": ("face.jpg", image_bytes, "image/jpeg")}
        r = requests.post(f"{self.base_url}/encode-face", files=files, timeout=20)
        try:
            response = r.json()
        except Exception:
            raise Exception(f"Face encoding failed: {r.text}")
        if response.get("success"):
            return response.get("embedding", "")
        raise Exception(response.get("message", "Face encoding failed"))

    def compare(self, emb1, emb2):
        import base64
        import numpy as np
        
        if isinstance(emb1, np.ndarray):
            emb1 = base64.b64encode(emb1.tobytes()).decode('utf-8')
        if isinstance(emb2, np.ndarray):
            emb2 = base64.b64encode(emb2.tobytes()).decode('utf-8')
            
        payload = {"embedding1": emb1, "embedding2": emb2}
        r = requests.post(f"{self.base_url}/compare-faces", json=payload, timeout=20)
        try:
            response = r.json()
        except Exception:
            raise Exception(f"Face comparison failed: {r.text}")
        if response.get("success"):
            return response
        else:
            raise Exception(response.get('message', 'Face comparison failed'))
=======
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
>>>>>>> 3486913fee80855a8b8bce9ab0e74324417a0c27
