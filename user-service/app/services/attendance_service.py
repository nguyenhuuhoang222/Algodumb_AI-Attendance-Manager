from typing import Dict, Any, List
from datetime import datetime, date
from ..repositories.user_repository import UserRepository
from ..repositories.attendance_repository import AttendanceRepository
from .face_recognition_service import FaceRecognitionService
from .storage_service import StorageService
from ..utils.image_processor import resize_image, validate_image_format
from ..utils.validators import validate_image_size
from ..utils.logger import logger
from ..config.settings import Config

class AttendanceService:
    # Service xử lý logic nghiệp vụ cho Attendance

    def __init__(self):
        self.user_repo = UserRepository()
        self.attendance_repo = AttendanceRepository()
        self.face_service = FaceRecognitionService()
        self.storage_service = StorageService()
    
    def mark_attendance_single(self, image_file, user_id: str = None, note: str = None) -> Dict[str, Any]:
        # Điểm danh cho 1 khuôn mặt
        try:
            # Validate ảnh
            image_bytes = image_file.read()
            image_file.seek(0)
            
            if not validate_image_format(image_bytes):
                return {"success": False, "error": "Định dạng ảnh không hợp lệ"}
            
            size_check = validate_image_size(image_file, 5242880)
            if not size_check["valid"]:
                return {"success": False, "error": size_check["message"]}
            
            # Resize ảnh
            resized_image = resize_image(image_bytes, (640, 480))
            
            # Gọi faceid-service để encode
            encode_result = self.face_service.encode_face(resized_image)
            if not encode_result["success"]:
                return {"success": False, "error": f"Lỗi nhận dạng khuôn mặt: {encode_result['error']}"}
            
            # Tìm user khớp
            if user_id:
                # Nếu có user_id, so sánh trực tiếp
                user = self.user_repo.get_user_by_id(user_id)
                if not user:
                    return {"success": False, "error": "Không tìm thấy học sinh"}
                
                compare_result = self.face_service.compare_faces(
                    encode_result["embedding"],
                    user.face_encoding
                )
                
                if not compare_result["success"] or not compare_result["match"]:
                    return {"success": False, "error": "Khuôn mặt không khớp với học sinh"}
                
                matched_user = user
            else:
                # Tìm trong tất cả users
                all_users = self.user_repo.get_all_users()
                user_dicts = [user.to_dict() for user in all_users]
                
                matches = self.face_service.find_matching_users(
                    encode_result["embedding"],
                    user_dicts,
                    Config.MATCH_THRESHOLD
                )
                
                if not matches:
                    return {"success": False, "error": "Không tìm thấy học sinh khớp"}
                
                matched_user = self.user_repo.get_user_by_id(matches[0]["user_id"])
            
            # Upload ảnh điểm danh
            today = date.today().strftime("%Y-%m-%d")
            attendance_image_url = self.storage_service.upload_attendance_image(
                resized_image,
                matched_user.id,
                today
            )
            
            if not attendance_image_url:
                return {"success": False, "error": "Lỗi upload ảnh điểm danh"}
            
            # Ghi điểm danh
            attendance_id = self.attendance_repo.upsert_daily_attendance(
                matched_user.id,
                today,
                "present",
                attendance_image_url,
                note
            )
            
            logger.log_face_recognition(
                "mark_attendance",
                user_id=matched_user.id,
                similarity=matches[0]["similarity"] if not user_id else compare_result["similarity"]
            )
            
            return {
                "success": True,
                "attendance_id": attendance_id,
                "user_id": matched_user.id,
                "name": matched_user.name,
                "email": matched_user.email,
                "similarity": matches[0]["similarity"] if not user_id else compare_result["similarity"],
                "message": "Điểm danh thành công"
            }
            
        except Exception as e:
            logger.log_error("Attendance marking error")
            return {"success": False, "error": f"Lỗi điểm danh: {str(e)}"}
    
    def mark_attendance_multi(self, image_file, note: str = None, class_id: str = None) -> Dict[str, Any]:
        # Điểm danh cho nhiều khuôn mặt trong 1 ảnh
        try:
            # 1. Validate ảnh
            image_bytes = image_file.read()
            image_file.seek(0)
            
            if not validate_image_format(image_bytes):
                return {"success": False, "error": "Định dạng ảnh không hợp lệ"}
            
            size_check = validate_image_size(image_file, 5242880)
            if not size_check["valid"]:
                return {"success": False, "error": size_check["message"]}
            
            # 2. Resize ảnh
            resized_image = resize_image(image_bytes, (640, 480))
            
            # 3. Gọi faceid-service để encode
            encode_result = self.face_service.encode_face(resized_image)
            if not encode_result["success"]:
                return {"success": False, "error": f"Lỗi nhận dạng khuôn mặt: {encode_result['error']}"}
            
            # 4. Tìm users khớp (có thể filter theo class_id nếu có)
            if class_id:
                # TODO: Implement filter by class_id when class management is added
                all_users = self.user_repo.get_all_users()
            else:
                all_users = self.user_repo.get_all_users()
            user_dicts = [user.to_dict() for user in all_users]
            
            matches = self.face_service.find_matching_users(
                encode_result["embedding"],
                user_dicts,
                Config.MATCH_THRESHOLD
            )
            
            if not matches:
                return {
                    "success": True,
                    "date": date.today().strftime("%Y-%m-%d"),
                    "results": [],
                    "message": "Không tìm thấy học sinh nào khớp"
                }
            
            # Xử lý từng match
            results = []
            today = date.today().strftime("%Y-%m-%d")
            
            for match in matches:
                try:
                    # Upload ảnh điểm danh
                    attendance_image_url = self.storage_service.upload_attendance_image(
                        resized_image,
                        match["user_id"],
                        f"{today}_{match['user_id']}.jpg"
                    )
                    
                    if attendance_image_url:
                        # Ghi điểm danh
                        attendance_id = self.attendance_repo.upsert_daily_attendance(
                            match["user_id"],
                            today,
                            "present",
                            attendance_image_url,
                            note
                        )
                        
                        # Lấy thông tin attendance record
                        attendance_record = self.attendance_repo.get_attendance_by_user_and_date(
                            match["user_id"],
                            today
                        )
                        
                        results.append({
                            "user_id": match["user_id"],
                            "name": match["name"],
                            "email": match["email"],
                            "similarity": match["similarity"],
                            "distance": match["distance"],
                            "matched": True,
                            "attendance_id": attendance_id,
                            "first_seen": attendance_record.first_seen.isoformat() if attendance_record else None,
                            "last_seen": attendance_record.last_seen.isoformat() if attendance_record else None,
                            "captures": attendance_record.captures if attendance_record else 0
                        })
                        
                        logger.log_face_recognition(
                            "mark_attendance_multi",
                            user_id=match["user_id"],
                            similarity=match["similarity"]
                        )
                        
                except Exception as e:
                    logger.log_error("Multi attendance error", user_id=match["user_id"])
                    results.append({
                        "user_id": match["user_id"],
                        "name": match["name"],
                        "email": match["email"],
                        "similarity": match["similarity"],
                        "distance": match["distance"],
                        "matched": False,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "date": today,
                "results": results,
                "message": f"Xử lý {len(results)} kết quả"
            }
            
        except Exception as e:
            logger.log_error("Multi attendance marking error")
            return {"success": False, "error": f"Lỗi điểm danh: {str(e)}"}
    
    def get_daily_attendance(self, attendance_date: str, limit: int = 100, class_id: str = None) -> Dict[str, Any]:
        # Lấy danh sách điểm danh theo ngày
        try:
            records = self.attendance_repo.get_attendance_by_date(attendance_date, limit)
            
            results = []
            for record in records:
                user = self.user_repo.get_user_by_id(record.user_id)
                if user:
                    # TODO: Filter by class_id when class management is implemented
                    # if class_id and user.class_id != class_id:
                    #     continue
                    
                    results.append({
                        "attendance_id": record.id,
                        "user_id": record.user_id,
                        "name": user.name,
                        "email": user.email,
                        "status": record.status,
                        "first_seen": record.first_seen.isoformat(),
                        "last_seen": record.last_seen.isoformat(),
                        "captures": record.captures,
                        "captured_image": record.captured_image,
                        "note": record.note
                    })
            
            return {
                "success": True,
                "date": attendance_date,
                "total": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.log_error("Get daily attendance error")
            return {"success": False, "error": f"Lỗi lấy danh sách: {str(e)}"}
    
    def get_user_attendance_history(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        # Lấy lịch sử điểm danh của học sinh
        try:
            records = self.attendance_repo.get_user_attendance_history(user_id, limit)
            
            results = []
            for record in records:
                results.append({
                    "attendance_id": record.id,
                    "date": record.user_id,  # This should be date field
                    "status": record.status,
                    "first_seen": record.first_seen.isoformat(),
                    "last_seen": record.last_seen.isoformat(),
                    "captures": record.captures,
                    "captured_image": record.captured_image,
                    "note": record.note
                })
            
            return {
                "success": True,
                "user_id": user_id,
                "total": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.log_error("Get user attendance error", user_id=user_id)
            return {"success": False, "error": f"Lỗi lấy lịch sử: {str(e)}"}
    
    def mark_absent_batch(self, user_ids: List[str], attendance_date: str) -> Dict[str, Any]:
        # Đánh dấu vắng hàng loạt
        try:
            created_count = self.attendance_repo.mark_absent_batch(user_ids, attendance_date)
            
            return {
                "success": True,
                "date": attendance_date,
                "created": created_count,
                "message": f"Đánh dấu {created_count} học sinh vắng mặt"
            }
            
        except Exception as e:
            logger.log_error("Batch absent marking error")
            return {"success": False, "error": f"Lỗi đánh dấu vắng: {str(e)}"}
