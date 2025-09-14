<<<<<<< HEAD
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    embedding: str  # Base64 encoded embedding
    student_id: Optional[str] = None
    full_name: Optional[str] = None
    class_name: Optional[str] = None
    email: Optional[str] = None
    image_path: Optional[str] = None

class LoginResult(BaseModel):
    username: str
    match: bool
    distance: float

class AttendanceRecord(BaseModel):
    student_id: str
    username: str
    full_name: str
    class_name: str
    timestamp: datetime
    status: str  # "present", "absent", "late"

class StudentInfo(BaseModel):
    student_id: str
    username: str
    full_name: str
    class_name: str
    last_attendance: Optional[datetime] = None
    attendance_status: str = "absent"  # "present", "absent", "late"
=======
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class User:
    # Model cho thông tin học sinh
    id: str
    name: str
    email: str
    face_encoding: List[float]
    image_path: str
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_dict(cls, data: dict, doc_id: str) -> 'User':
        # Tạo User từ Firestore document    
        return cls(
            id=doc_id,
            name=data.get('name', ''),
            email=data.get('email', ''),
            face_encoding=data.get('face_encoding', []),
            image_path=data.get('image_path', ''),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self) -> dict:
        # Chuyển User thành dict cho Firestore
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'face_encoding': self.face_encoding,
            'image_path': self.image_path,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

@dataclass
class AttendanceRecord:
    # Model cho bản ghi điểm danh
    id: str
    user_id: str
    status: str  # "present" hoặc "absent"
    captured_image: str
    timestamp: datetime  # Thời gian điểm danh (thời gian thực)
    note: Optional[str] = None
    
    # Các trường bổ sung cho tracking chi tiết
    first_seen: Optional[datetime] = None  # Lần đầu thấy (nếu có)
    last_seen: Optional[datetime] = None   # Lần cuối thấy (nếu có)
    captures: int = 1  # Số lần chụp (mặc định 1)
    
    @classmethod
    def from_dict(cls, data: dict, doc_id: str) -> 'AttendanceRecord':
        # Tạo AttendanceRecord từ Firestore document
        return cls(
            id=doc_id,
            user_id=data.get('user_id', ''),
            status=data.get('status', ''),
            captured_image=data.get('captured_image', ''),
            timestamp=data.get('timestamp'),
            note=data.get('note'),
            first_seen=data.get('first_seen'),
            last_seen=data.get('last_seen'),
            captures=data.get('captures', 1)
        )
    
    def to_dict(self) -> dict:
        # Chuyển AttendanceRecord thành dict cho Firestore
        return {
            'user_id': self.user_id,
            'status': self.status,
            'captured_image': self.captured_image,
            'timestamp': self.timestamp,
            'note': self.note,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'captures': self.captures
        }
>>>>>>> 3486913fee80855a8b8bce9ab0e74324417a0c27
