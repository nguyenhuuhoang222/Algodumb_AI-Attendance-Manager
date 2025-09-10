# Gọi faceid-service qua HTTP
import requests
import json
from typing import List

class FaceAuthService:
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
        return r.json()
