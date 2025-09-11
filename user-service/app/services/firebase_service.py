# Kết nối Firestore/Storage (đơn giản hoá)
# Đặt biến môi trường:
#   GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
#   FIREBASE_PROJECT_ID=your_project_id
from typing import Optional
from google.cloud import firestore
import os

class FirebaseService:
    # Service để kết nối và tương tác với Firebase Firestore

    def __init__(self):
        # 1. Lấy project ID từ environment variable
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        # 2. Tạo client mặc định (sử dụng GOOGLE_APPLICATION_CREDENTIALS)
        self.db = firestore.Client(project=project_id) if project_id else None

    def save_user(self, user):
        # Lưu thông tin user vào Firestore hoặc file local
        if not self.db:
            # 3. Chế độ demo: lưu tạm vào file JSON cục bộ
            os.makedirs("user-service_data", exist_ok=True)
            path = os.path.join("user-service_data", f"{user.username}.json")
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"username": user.username, "embedding": user.embedding}, f, ensure_ascii=False)
            return
        # 4. Lưu vào Firestore collection "users"
        self.db.collection("users").document(user.username).set({
            "username": user.username,
            "embedding": user.embedding
        })

    def get_user(self, username: str) -> Optional[dict]:
        # Lấy thông tin user từ Firestore hoặc file local
        if not self.db:
            # 5. Chế độ demo: đọc từ file JSON cục bộ
            path = os.path.join("user-service_data", f"{username}.json")
            if os.path.exists(path):
                import json
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        # 6. Đọc từ Firestore collection "users"
        doc = self.db.collection("users").document(username).get()
        return doc.to_dict() if doc.exists else None
