from google.cloud import firestore
from typing import Optional, List
from datetime import datetime, date
from ..models.user_models import AttendanceRecord
from ..config.settings import Config

class AttendanceRepository:
    # Repository handling Attendance data in Firestore

    def __init__(self):
        self.db = firestore.Client(project=Config.FIREBASE_PROJECT_ID)
        self.collection = "attendance"
    
    def create_attendance_record(self, attendance_data: dict) -> str:
        # Create new attendance record
        doc_ref = self.db.collection(self.collection).document()
        doc_ref.set(attendance_data)
        return doc_ref.id
    
    def get_attendance_by_user_and_date(self, user_id: str, attendance_date: str) -> Optional[AttendanceRecord]:
        # Get attendance record by user and date
        query = (self.db.collection(self.collection)
                 .where("user_id", "==", user_id)
                 .where("date", "==", attendance_date)
                 .limit(1))
        
        docs = query.stream()
        for doc in docs:
            return AttendanceRecord.from_dict(doc.to_dict(), doc.id)
        return None
    
    def upsert_daily_attendance(self, user_id: str, attendance_date: str, status: str, 
                               captured_image: str, note: str = None) -> str:
        # Upsert attendance by date (idempotent)
        try:
            # Find current record
            existing_record = self.get_attendance_by_user_and_date(user_id, attendance_date)
            
            if existing_record:
                # Update current record
                update_data = {
                    "last_seen": datetime.utcnow(),
                    "captures": existing_record.captures + 1,
                    "captured_image": captured_image,
                    "note": note or existing_record.note
                }
                
                # Find document ID of current record
                query = (self.db.collection(self.collection)
                         .where("user_id", "==", user_id)
                         .where("date", "==", attendance_date)
                         .limit(1))
                
                docs = query.stream()
                for doc in docs:
                    doc.reference.update(update_data)
                    return doc.id
            else:
                # Create new record
                now = datetime.utcnow()
                attendance_data = {
                    "user_id": user_id,
                    "date": attendance_date,
                    "status": status,
                    "first_seen": now,
                    "last_seen": now,
                    "captures": 1,
                    "captured_image": captured_image,
                    "note": note,
                    "created_at": now
                }
                
                doc_ref = self.db.collection(self.collection).document()
                doc_ref.set(attendance_data)
                return doc_ref.id
                
        except Exception as e:
            raise Exception(f"Upsert attendance error: {str(e)}")
    
    def get_attendance_by_date(self, attendance_date: str, limit: int = 100) -> List[AttendanceRecord]:
        # Get attendance list by date
        query = (self.db.collection(self.collection)
                 .where("date", "==", attendance_date)
                 .order_by("last_seen", direction=firestore.Query.DESCENDING)
                 .limit(limit))
        
        docs = query.stream()
        return [AttendanceRecord.from_dict(doc.to_dict(), doc.id) for doc in docs]
    
    def get_user_attendance_history(self, user_id: str, limit: int = 50) -> List[AttendanceRecord]:
        # Get user attendance history
        query = (self.db.collection(self.collection)
                 .where("user_id", "==", user_id)
                 .order_by("date", direction=firestore.Query.DESCENDING)
                 .limit(limit))
        
        docs = query.stream()
        return [AttendanceRecord.from_dict(doc.to_dict(), doc.id) for doc in docs]
    
    def mark_absent_batch(self, user_ids: List[str], attendance_date: str) -> int:
        # Mark absent in bulk for user list
        created_count = 0
        batch = self.db.batch()
        
        for user_id in user_ids:
            # Check if attendance record already exists
            existing = self.get_attendance_by_user_and_date(user_id, attendance_date)
            if not existing:
                doc_ref = self.db.collection(self.collection).document()
                attendance_data = {
                    "user_id": user_id,
                    "date": attendance_date,
                    "status": "absent",
                    "first_seen": datetime.utcnow(),
                    "last_seen": datetime.utcnow(),
                    "captures": 0,
                    "captured_image": "",
                    "note": "Automatically marked absent",
                    "created_at": datetime.utcnow()
                }
                batch.set(doc_ref, attendance_data)
                created_count += 1
        
        if created_count > 0:
            batch.commit()
        
        return created_count
    
    def get_attendance_stats(self, start_date: str, end_date: str) -> dict:
        # Get attendance statistics in time range
        query = (self.db.collection(self.collection)
                 .where("date", ">=", start_date)
                 .where("date", "<=", end_date))
        
        docs = query.stream()
        stats = {
            "total_records": 0,
            "present_count": 0,
            "absent_count": 0,
            "unique_users": set()
        }
        
        for doc in docs:
            data = doc.to_dict()
            stats["total_records"] += 1
            stats["unique_users"].add(data.get("user_id"))
            
            if data.get("status") == "present":
                stats["present_count"] += 1
            elif data.get("status") == "absent":
                stats["absent_count"] += 1
        
        stats["unique_users"] = len(stats["unique_users"])
        return stats
