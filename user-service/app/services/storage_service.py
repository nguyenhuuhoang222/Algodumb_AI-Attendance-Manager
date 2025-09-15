from google.cloud import storage
from typing import Optional
from ..config.settings import Config
from ..utils.logger import logger

class StorageService:
    # Service handling image upload to Firebase Storage

    def __init__(self):
        self.client = storage.Client(project=Config.FIREBASE_PROJECT_ID)
        # Try different bucket name
        self.bucket_name = "algodumb-22983.appspot.com"
        # Or try: "gs://algodumb-22983.appspot.com"
        self.bucket = self.client.bucket(self.bucket_name)
    
    def upload_image(self, image_bytes: bytes, file_path: str) -> Optional[str]:
        # Upload image to Firebase Storage and return public URL
        try:
            # Temporarily use local storage
            import os
            local_path = f"uploads/{file_path}"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, 'wb') as f:
                f.write(image_bytes)
            
            # Return temporary local URL
            public_url = f"http://localhost:5002/{local_path}"
            
            logger.log_request("upload_image", f"/storage/{file_path}")
            return public_url
            
        except Exception as e:
            logger.log_error(str(e))
            return None
    
    def upload_face_image(self, image_bytes: bytes, user_id: str, filename: str = None) -> Optional[str]:
        # Upload face image for user
        if not filename:
            filename = f"face_{user_id}.jpg"
        
        file_path = f"faces/{user_id}/{filename}"
        return self.upload_image(image_bytes, file_path)
    
    def upload_attendance_image(self, image_bytes: bytes, user_id: str, attendance_date: str) -> Optional[str]:
        # Upload attendance image
        filename = f"attendance_{attendance_date}_{user_id}.jpg"
        file_path = f"attendance/{attendance_date}/{user_id}/{filename}"
        return self.upload_image(image_bytes, file_path)
    
    def delete_image(self, file_path: str) -> bool:
        # Delete image from Storage
        try:
            blob = self.bucket.blob(file_path)
            blob.delete()
            return True
        except Exception as e:
            logger.log_error(str(e))
            return False
    
    def get_image_url(self, file_path: str) -> Optional[str]:
        # Get public URL of image
        try:
            blob = self.bucket.blob(file_path)
            if blob.exists():
                return blob.public_url
            return None
        except Exception as e:
            logger.log_error(str(e))
            return None
