from google.cloud import firestore
from typing import Optional, List
from datetime import datetime
from ..models.user_models import User
from ..config.settings import Config

class UserRepository:
    # Repository handling User data in Firestore

    def __init__(self):
        self.db = firestore.Client(project=Config.FIREBASE_PROJECT_ID)
        self.collection = "users"
    
    def create_user(self, user_data: dict) -> str:
        # Create new user in Firestore
        # 1. Add timestamp
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        
        # 2. Create new document and save
        doc_ref = self.db.collection(self.collection).document()
        doc_ref.set(user_data)
        # 3. Return document ID
        return doc_ref.id
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        # Get user by ID
        doc = self.db.collection(self.collection).document(user_id).get()
        if doc.exists:
            return User.from_dict(doc.to_dict(), doc.id)
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        # Get user by email
        query = self.db.collection(self.collection).where("email", "==", email).limit(1)
        docs = query.stream()
        
        for doc in docs:
            return User.from_dict(doc.to_dict(), doc.id)
        return None
    
    def get_all_users(self) -> List[User]:
        # Get all users
        docs = self.db.collection(self.collection).stream()
        return [User.from_dict(doc.to_dict(), doc.id) for doc in docs]
    
    def update_user(self, user_id: str, update_data: dict) -> bool:
        # Update user information
        try:
            update_data["updated_at"] = datetime.utcnow()
            self.db.collection(self.collection).document(user_id).update(update_data)
            return True
        except Exception:
            return False
    
    def update_user_face(self, user_id: str, face_encoding: list, image_path: str) -> bool:
        # Update face encoding and image for user
        try:
            update_data = {
                "face_encoding": face_encoding,
                "image_path": image_path,
                "updated_at": datetime.utcnow()
            }
            self.db.collection(self.collection).document(user_id).update(update_data)
            return True
        except Exception:
            return False
    
    
    def search_users_by_name(self, name: str) -> List[User]:
        # Search users by name
        query = self.db.collection(self.collection).where("name", ">=", name).where("name", "<=", name + "\uf8ff")
        docs = query.stream()
        return [User.from_dict(doc.to_dict(), doc.id) for doc in docs]
