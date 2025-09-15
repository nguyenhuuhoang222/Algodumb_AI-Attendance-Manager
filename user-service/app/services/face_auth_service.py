<<<<<<< HEAD
# Gọi faceid-service qua HTTP
=======
# Call faceid-service via HTTP
>>>>>>> clean-branch
import requests
import json
from typing import List

class FaceAuthService:
<<<<<<< HEAD
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def encode(self, image_bytes: bytes) -> List[float]:
        files = {"file": ("face.jpg", image_bytes, "image/jpeg")}
        r = requests.post(f"{self.base_url}/encode-face", files=files, timeout=20)
        r.raise_for_status()
        return r.json().get("embedding", [])

    def compare(self, emb1, emb2):
        payload = {"emb1": emb1, "emb2": emb2}
        r = requests.post(f"{self.base_url}/compare-faces", json=payload, timeout=20)
        r.raise_for_status()
=======
    # Service calling faceid-service to handle face recognition 

    def __init__(self, base_url: str):
        # 1. Initialize base URL for faceid-service
        self.base_url = base_url.rstrip("/")

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
    def encode(self, image_bytes: bytes) -> List[float]:
        # Call faceid-service to encode face
        # 2. Prepare file upload
        files = {"file": ("face.jpg", image_bytes, "image/jpeg")}
        # 3. Call API encode-face
        r = requests.post(f"{self.base_url}/encode-face", files=files, timeout=20)
        r.raise_for_status()
        # 4. Return embedding vector
        return r.json().get("embedding", [])

    def compare(self, emb1, emb2):
        # Call faceid-service to compare 2 embeddings
        # 5. Prepare payload
        payload = {"emb1": emb1, "emb2": emb2}
        # 6. Call API compare-faces
        r = requests.post(f"{self.base_url}/compare-faces", json=payload, timeout=20)
        r.raise_for_status()
        # 7. Return comparison result
>>>>>>> clean-branch
        return r.json()
