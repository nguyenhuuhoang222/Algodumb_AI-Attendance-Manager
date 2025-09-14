import requests
import base64
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIController:
    
    def __init__(self, 
                 faceid_url: str = "http://localhost:5000",
                 user_url: str = "http://localhost:5002"):
        self.faceid_url = faceid_url.rstrip("/")
        self.user_url = user_url.rstrip("/")
        self.timeout = 30
        self.max_retries = 3
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault('timeout', self.timeout)
        
        for attempt in range(self.max_retries):
            try:
                response = requests.request(method, url, **kwargs)
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise e
                continue
        
        raise Exception("Max retries exceeded")
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        try:
            data = response.json()
        except Exception:
            data = {"message": response.text}
        
        if response.status_code == 200:
            return data
        else:
            error_msg = data.get("message", f"HTTP {response.status_code}")
            raise Exception(error_msg)
    
    def check_faceid_service(self) -> bool:
        try:
            response = self._make_request("GET", f"{self.faceid_url}/health")
            data = self._handle_response(response)
            return data.get("status") == "healthy"
        except Exception as e:
            logger.error(f"FaceID service check failed: {str(e)}")
            return False
    
    def check_user_service(self) -> bool:
        try:
            response = self._make_request("GET", f"{self.user_url}/api/students")
            return response.status_code in [200, 500]
        except Exception as e:
            logger.error(f"User service check failed: {str(e)}")
            return False
    
    def encode_face_single(self, image_bytes: bytes, 
                          min_liveness: float = 0.15, 
                          allow_mask: bool = False) -> Dict[str, Any]:
        try:
            files = {"image": ("face.jpg", image_bytes, "image/jpeg")}
            data = {
                "min_liveness": str(min_liveness),
                "allow_mask": "1" if allow_mask else "0"
            }
            
            response = self._make_request("POST", f"{self.faceid_url}/encode-face", 
                                        files=files, data=data)
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Face encoding failed: {str(e)}")
            raise Exception(f"Face encoding failed: {str(e)}")
    
    def encode_face_sequence(self, frames: List[bytes], 
                            min_liveness: float = 0.15, 
                            allow_mask: bool = False) -> Dict[str, Any]:
        try:
            files = []
            for i, frame_bytes in enumerate(frames[:30]):
                files.append(("frames", (f"frame{i}.jpg", frame_bytes, "image/jpeg")))
            
            data = {
                "min_liveness": str(min_liveness),
                "allow_mask": "1" if allow_mask else "0"
            }
            
            response = self._make_request("POST", f"{self.faceid_url}/encode-face", 
                                        files=files, data=data)
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Face sequence encoding failed: {str(e)}")
            raise Exception(f"Face sequence encoding failed: {str(e)}")
    
    def compare_faces(self, embedding1: str, embedding2: str, 
                     threshold: float = 0.8) -> Dict[str, Any]:
        try:
            payload = {
                "embedding1": embedding1,
                "embedding2": embedding2,
                "threshold": threshold
            }
            
            response = self._make_request("POST", f"{self.faceid_url}/compare-faces", 
                                        json=payload)
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Face comparison failed: {str(e)}")
            raise Exception(f"Face comparison failed: {str(e)}")
    
    def get_students_list(self) -> Dict[str, Any]:
        try:
            response = self._make_request("GET", f"{self.user_url}/api/students")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Get students list failed: {str(e)}")
            return {"students": [], "attendance": [], "storage": "unknown"}
    
    def register_student(self, student_data: Dict[str, Any], 
                        image_bytes: Optional[bytes] = None,
                        frames: Optional[List[bytes]] = None) -> Dict[str, Any]:
        try:
            form_data = {
                'student_id': student_data.get('student_id', ''),
                'full_name': student_data.get('full_name', ''),
                'class_name': student_data.get('class_name', ''),
                'username': student_data.get('username', ''),
                'email': student_data.get('email', '')
            }
            
            form_data = {k: v for k, v in form_data.items() if v}
            
            if frames and len(frames) >= 3:
                files = []
                for i, frame_bytes in enumerate(frames[:20]):
                    files.append(("frames", (f"frame{i}.jpg", frame_bytes, "image/jpeg")))
                response = self._make_request("POST", f"{self.user_url}/api/register-student", 
                                            files=files, data=form_data)
            elif image_bytes:
                files = {"file": ("face.jpg", image_bytes, "image/jpeg")}
                response = self._make_request("POST", f"{self.user_url}/api/register-student", 
                                            files=files, data=form_data)
            else:
                raise Exception("No image data provided")
            
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Student registration failed: {str(e)}")
            raise Exception(f"Student registration failed: {str(e)}")
    
    def checkin_student(self, image_bytes: bytes) -> Dict[str, Any]:
        try:
            files = {"file": ("face.jpg", image_bytes, "image/jpeg")}
            response = self._make_request("POST", f"{self.user_url}/api/checkin", files=files)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Check-in failed: {str(e)}")
            raise Exception(f"Check-in failed: {str(e)}")
    
    def checkout_student(self, image_bytes: bytes) -> Dict[str, Any]:
        try:
            files = {"file": ("face.jpg", image_bytes, "image/jpeg")}
            response = self._make_request("POST", f"{self.user_url}/api/checkout", files=files)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Check-out failed: {str(e)}")
            raise Exception(f"Check-out failed: {str(e)}")
    
    def get_attendance_summary(self, date_str: str) -> Dict[str, Any]:
        try:
            params = {"date": date_str}
            response = self._make_request("GET", f"{self.user_url}/api/attendance-summary", 
                                        params=params)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Get attendance summary failed: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def check_student_attendance_status(self, student_id: str, date_str: str) -> str:
        try:
            summary_res = self.get_attendance_summary(date_str)
            if summary_res.get("success"):
                summary = summary_res.get("summary", [])
                for item in summary:
                    if item.get("student_id") == student_id:
                        has_checkin = bool(item.get("checkin"))
                        has_checkout = bool(item.get("checkout"))
                        if has_checkin and has_checkout:
                            return "completed"
                        elif has_checkin:
                            return "checked_in"
                        else:
                            return "not_checked"
            return "not_checked"
        except Exception as e:
            logger.error(f"Check attendance status failed: {str(e)}")
            return "error"
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        try:
            students_data = self.get_students_list()
            students = students_data.get("students", [])
            attendance = students_data.get("attendance", [])
            
            total_students = len(students)
            present_today = len([a for a in attendance if a.get("type") in ["checkin", "attendance"]])
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            return {
                "total_students": total_students,
                "present_today": present_today,
                "attendance_rate": (present_today / total_students * 100) if total_students > 0 else 0,
                "students": students,
                "attendance": attendance,
                "date": today
            }
        except Exception as e:
            logger.error(f"Get dashboard data failed: {str(e)}")
            return {
                "total_students": 0,
                "present_today": 0,
                "attendance_rate": 0,
                "students": [],
                "attendance": [],
                "date": datetime.now().strftime("%Y-%m-%d")
            }

api_controller = APIController()