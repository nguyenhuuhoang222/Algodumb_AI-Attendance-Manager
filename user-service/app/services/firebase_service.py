# Connect to Firestore/Storage (simplified)
# Set environment variables:
#   GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
#   FIREBASE_PROJECT_ID=your_project_id
from typing import Optional, List, Dict, Any
from google.cloud import firestore
from google.oauth2 import service_account
import os
import json
from datetime import datetime

class FirebaseService:
    # Service để kết nối và tương tác với Firebase Firestore

    def __init__(self):
<<<<<<< HEAD
        env_project_id = os.getenv("FIREBASE_PROJECT_ID")
        env_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        default_credentials_path = os.path.join(
            repo_root, "algodumb-22983-firebase-adminsdk-fbsvc-c5d08813da.json"
        )

        credentials_obj = None
        project_id = env_project_id
        credentials_path = env_credentials_path

        if not project_id:
            project_id = "algodumb-22983"
        if not credentials_path and os.path.exists(default_credentials_path):
            credentials_path = default_credentials_path

        self.project_id = project_id
        self.credentials_path = credentials_path
        self.init_error = None

        try:
            if credentials_path and os.path.exists(credentials_path):
                credentials_obj = service_account.Credentials.from_service_account_file(credentials_path)
                self.db = firestore.Client(project=project_id, credentials=credentials_obj)
            else:
                self.db = firestore.Client(project=project_id) if project_id else None
        except Exception as e:
            self.db = None
            self.init_error = str(e)

    def _ensure_db(self):
        if not self.db:
            details = {
                "project_id": self.project_id,
                "credentials_path": self.credentials_path,
                "init_error": self.init_error or "project_id missing"
            }
            raise RuntimeError(
                f"Firestore not configured. Set FIREBASE_PROJECT_ID and GOOGLE_APPLICATION_CREDENTIALS. Details: {details}"
            )

    def save_user(self, user):
        self._ensure_db()
        user_data = {
=======
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
>>>>>>> 3486913fee80855a8b8bce9ab0e74324417a0c27
            "username": user.username,
            "embedding": user.embedding,
            "student_id": getattr(user, 'student_id', None),
            "full_name": getattr(user, 'full_name', None),
            "class_name": getattr(user, 'class_name', None),
            "email": getattr(user, 'email', None),
            "image_path": getattr(user, 'image_path', None),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self.db.collection("users").document(user.username).set(user_data)

    def get_user(self, username: str) -> Optional[dict]:
<<<<<<< HEAD
        self._ensure_db()
=======
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
>>>>>>> 3486913fee80855a8b8bce9ab0e74324417a0c27
        doc = self.db.collection("users").document(username).get()
        return doc.to_dict() if doc.exists else None
    
    def get_all_users(self) -> List[str]:
        """Get list of all usernames"""
        self._ensure_db()
        docs = self.db.collection("users").stream()
        return [doc.id for doc in docs]

    def get_mode_info(self) -> Dict[str, Any]:
        return {
            "mode": "firestore" if self.db else "local",
            "project_id": self.project_id,
            "credentials_path": self.credentials_path,
            "init_error": getattr(self, "init_error", None)
        }
    
    def get_all_students(self) -> List[Dict]:
        """Get list of all students"""
        self._ensure_db()
        docs = self.db.collection("users").stream()
        students = []
        for doc in docs:
            data = doc.to_dict()
            
            if data.get('student_id') and data.get('full_name'):
                student = {
                    'student_id': data.get('student_id'),
                    'username': data.get('username', data.get('student_id')),
                    'full_name': data.get('full_name'),
                    'class_name': data.get('class_name', 'Unassigned'),
                    'embedding': data.get('embedding', '')
                }
                students.append(student)
            
            elif data.get('name') and data.get('email'):
                embedding_base64 = data.get('face_encoding', '')
                
                student = {
                    'student_id': data.get('email', 'unknown'),
                    'username': data.get('email', 'unknown'),
                    'full_name': data.get('name', 'Unknown'),
                    'class_name': 'Unassigned',
                    'embedding': embedding_base64
                }
                students.append(student)
        
        return students
    
    def save_attendance(self, student_id: str, timestamp: datetime):
        """Save attendance record"""
        self._ensure_db()
        attendance_data = {
            "student_id": student_id,
            "date": timestamp.strftime("%Y-%m-%d"),
            "timestamp": timestamp.isoformat(),
            "status": "present"
        }
        self.db.collection("attendance").add(attendance_data)
        return True

    def save_attendance_event(self, student_id: str, timestamp: datetime, event_type: str):
        """Save attendance event: checkin/checkout"""
        self._ensure_db()
        data = {
            "student_id": student_id,
            "date": timestamp.strftime("%Y-%m-%d"),
            "timestamp": timestamp.isoformat(),
            "type": event_type
        }
        print(f"DEBUG: Saving attendance event: {data}")
        doc_ref = self.db.collection("attendance").add(data)
        print(f"DEBUG: Attendance event saved with doc_ref: {doc_ref}")
        return True
    
    def get_attendance_today(self) -> List[Dict]:
        """Get today's attendance list"""
        self._ensure_db()
        today = datetime.now().strftime("%Y-%m-%d")
        docs = self.db.collection("attendance").where("date", "==", today).stream()
        return [doc.to_dict() for doc in docs]

    def get_today_events_for_student(self, student_id: str) -> List[Dict]:
        """Get all today's events for a student (checkin/checkout)."""
        self._ensure_db()
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"DEBUG: Getting events for student {student_id} on {today}")
        docs = self.db.collection("attendance").where("date", "==", today).where("student_id", "==", student_id).stream()
        events = [doc.to_dict() for doc in docs]
        print(f"DEBUG: Found {len(events)} events for student {student_id}: {events}")
        return events

    def has_checked_in_today(self, student_id: str) -> bool:
        events = self.get_today_events_for_student(student_id)
        return any(e.get("type") == "checkin" for e in events)

    def has_checked_out_today(self, student_id: str) -> bool:
        events = self.get_today_events_for_student(student_id)
        return any(e.get("type") == "checkout" for e in events)
    
    def has_attendance_today(self, student_id: str) -> bool:
        """Check if student has attended today"""
        events = self.get_today_events_for_student(student_id)
        return any(e.get("type") == "attendance" for e in events)

    def get_attendance_by_date(self, date_str: str) -> List[Dict]:
        """Get all attendance records by date (including type)."""
        self._ensure_db()
        docs = self.db.collection("attendance").where("date", "==", date_str).stream()
        return [doc.to_dict() for doc in docs]

    def summarize_sessions(self, date_str: str) -> List[Dict]:
        """Summarize sessions by student: first checkin, last checkout, duration (minutes)."""
        self._ensure_db()
        records = self.get_attendance_by_date(date_str)
        by_student: Dict[str, List[Dict]] = {}
        for r in records:
            by_student.setdefault(r.get("student_id", "unknown"), []).append(r)
        summary = []
        for sid, items in by_student.items():
            items_sorted = sorted(items, key=lambda x: x.get("timestamp", ""))
            checkin = next((i for i in items_sorted if i.get("type") == "checkin"), None)
            checkout = next((i for i in reversed(items_sorted) if i.get("type") == "checkout"), None)
            duration_min = 0
            if checkin and checkout:
                try:
                    t1 = datetime.fromisoformat(checkin["timestamp"])
                    t2 = datetime.fromisoformat(checkout["timestamp"])
                    duration_min = int((t2 - t1).total_seconds() // 60)
                except Exception:
                    duration_min = 0
            summary.append({
                "student_id": sid,
                "date": date_str,
                "checkin": checkin.get("timestamp") if checkin else None,
                "checkout": checkout.get("timestamp") if checkout else None,
                "duration_min": duration_min
            })
        return summary