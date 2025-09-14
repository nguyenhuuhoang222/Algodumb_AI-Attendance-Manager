from typing import Dict, Any, Optional
from ..repositories.user_repository import UserRepository
from .face_recognition_service import FaceRecognitionService
from .storage_service import StorageService
from ..utils.image_processor import resize_image, validate_image_format
from ..utils.validators import validate_image_size
from ..utils.logger import logger
from ..models.user_models import User

class UserService:
    # Service xử lý logic nghiệp vụ cho User

    def __init__(self):
        self.user_repo = UserRepository()
        self.face_service = FaceRecognitionService()
        self.storage_service = StorageService()
    
    def register_user(self, name: str, email: str, image_file) -> Dict[str, Any]:
        # Đăng ký học sinh mới với thông tin cơ bản và ảnh khuôn mặt
        try:
            # 1. Validate ảnh
            image_bytes = image_file.read()
            image_file.seek(0)  # Reset file pointer
            
            if not validate_image_format(image_bytes):
                return {"success": False, "error": "Định dạng ảnh không hợp lệ"}
            
            size_check = validate_image_size(image_file, 5242880)  # 5MB
            if not size_check["valid"]:
                return {"success": False, "error": size_check["message"]}
            
            # 2. Resize ảnh
            resized_image = resize_image(image_bytes, (640, 480))
            
            # 3. Gọi faceid-service để encode
            encode_result = self.face_service.encode_face(resized_image)
            if not encode_result["success"]:
                return {"success": False, "error": f"Lỗi nhận dạng khuôn mặt: {encode_result['error']}"}
            
            # 4. Upload ảnh lên Storage
            image_url = self.storage_service.upload_face_image(
                resized_image, 
                email, 
                f"face_{email}.jpg"
            )
            
            if not image_url:
                return {"success": False, "error": "Lỗi upload ảnh lên Storage"}
            
            # 5. Lưu vào database
            user_data = {
                "name": name,
                "email": email,
                "face_encoding": encode_result["embedding"],
                "image_path": image_url
            }
            
            user_id = self.user_repo.create_user(user_data)
            
            logger.log_face_recognition("register_user", user_id=user_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "name": name,
                "email": email,
                "image_path": image_url,
                "message": "Đăng ký thành công"
            }
            
        except Exception as e:
            logger.log_error("User registration error")
            return {"success": False, "error": f"Lỗi đăng ký: {str(e)}"}
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        # Lấy thông tin học sinh theo email
        return self.user_repo.get_user_by_email(email)
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        # Lấy thông tin học sinh theo ID
        return self.user_repo.get_user_by_id(user_id)
    
    def update_user_face(self, user_id: str, image_file) -> Dict[str, Any]:
        # Cập nhật ảnh khuôn mặt cho học sinh đã có
        try:
            # Validate ảnh
            image_bytes = image_file.read()
            image_file.seek(0)
            
            if not validate_image_format(image_bytes):
                return {"success": False, "error": "Định dạng ảnh không hợp lệ"}
            
            # Resize ảnh
            resized_image = resize_image(image_bytes, (640, 480))
            
            # Gọi faceid-service để encode
            encode_result = self.face_service.encode_face(resized_image)
            if not encode_result["success"]:
                return {"success": False, "error": f"Lỗi nhận dạng khuôn mặt: {encode_result['error']}"}
            
            # Upload ảnh mới
            user = self.user_repo.get_user_by_id(user_id)
            if not user:
                return {"success": False, "error": "Không tìm thấy user"}
            
            image_url = self.storage_service.upload_face_image(
                resized_image,
                user_id,
                f"face_{user_id}_updated.jpg"
            )
            
            if not image_url:
                return {"success": False, "error": "Lỗi upload ảnh lên Storage"}
            
            # Cập nhật database
            success = self.user_repo.update_user_face(
                user_id,
                encode_result["embedding"],
                image_url
            )
            
            if success:
                logger.log_face_recognition("update_face", user_id=user_id)
                return {"success": True, "message": "Cập nhật ảnh thành công"}
            else:
                return {"success": False, "error": "Lỗi cập nhật database"}
                
        except Exception as e:
            logger.log_error("Face update error", user_id=user_id)
            return {"success": False, "error": f"Lỗi cập nhật: {str(e)}"}
    
    def get_all_users(self) -> list:
        # Lấy danh sách tất cả học sinh
        return self.user_repo.get_all_users()
    
    def search_users_by_name(self, name: str) -> list:
        # Tìm kiếm học sinh theo tên
        return self.user_repo.search_users_by_name(name)
    
