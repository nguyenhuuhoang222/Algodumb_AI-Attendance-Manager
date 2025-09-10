# Kết nối Firestore/Storage (đơn giản hoá)
# Đặt biến môi trường:
#   GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
#   FIREBASE_PROJECT_ID=your_project_id
from typing import Optional
from google.cloud import firestore
import os

class FirebaseService:
    def __init__(self):
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        # Tạo client mặc định (sử dụng GOOGLE_APPLICATION_CREDENTIALS)
        self.db = firestore.Client(project=project_id) if project_id else None

    def save_user(self, user):
        if not self.db:
            # Chế độ demo: lưu tạm vào file JSON cục bộ
            os.makedirs("user-service_data", exist_ok=True)
            path = os.path.join("user-service_data", f"{user.username}.json")
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"username": user.username, "embedding": user.embedding}, f, ensure_ascii=False)
            return
        self.db.collection("users").document(user.username).set({
            "username": user.username,
            "embedding": user.embedding
        })

    def get_user(self, username: str) -> Optional[dict]:
        if not self.db:
            path = os.path.join("user-service_data", f"{username}.json")
            if os.path.exists(path):
                import json
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        doc = self.db.collection("users").document(username).get()
        return doc.to_dict() if doc.exists else None
