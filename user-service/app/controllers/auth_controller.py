<<<<<<< HEAD

# Face-based registration/login
from flask import Blueprint, request, jsonify
from ..services.face_auth_service import FaceAuthService
from ..services.firebase_service import FirebaseService
from ..models.user_models import UserCreate, LoginResult, StudentInfo, AttendanceRecord
from datetime import datetime

auth_bp = Blueprint("auth", __name__)
face_auth = FaceAuthService(base_url="http://localhost:5000")
db = FirebaseService()  # Read config from environment variables

@auth_bp.route("/register-face", methods=["POST"])
def register_face():
    file = request.files.get("file")
    username = request.form.get("username")
    if not file or not username:
        return jsonify({"error":"Missing file or username"}), 400

    emb = face_auth.encode(file.stream.read())
    user = UserCreate(username=username, embedding=emb)
    db.save_user(user)
    return jsonify({"ok": True})

@auth_bp.route("/login-face", methods=["POST"])
def login_face():
    file = request.files.get("file")
    username = request.form.get("username")
    if not file or not username:
        return jsonify({"error":"Missing file or username"}), 400

    saved = db.get_user(username)
    if not saved:
        return jsonify({"error":"User does not exist"}), 404

    emb_live = face_auth.encode(file.stream.read())
    match = face_auth.compare(saved["embedding"], emb_live)
    res = LoginResult(username=username, match=match["match"], distance=match["distance"])
    return jsonify(res.model_dump())

@auth_bp.route("/students", methods=["GET"])
def get_students():
    """Get student list and today's attendance"""
    try:
        students = db.get_all_students()
        attendance = db.get_attendance_today()
        mode = db.get_mode_info()
        
        print(f"DEBUG: /students API - Found {len(students)} students, {len(attendance)} attendance records")
        for att in attendance:
            print(f"DEBUG: Attendance record - student_id: {att.get('student_id')}, type: {att.get('type')}, timestamp: {att.get('timestamp')}")
        
        return jsonify({
            "students": students,
            "attendance": attendance,
            "storage": mode
        })
    except Exception as e:
        print(f"DEBUG: /students API error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth_bp.route("/register-student", methods=["POST"])
def register_student():
    """Register new student with complete information"""
    try:
        student_id = request.form.get("student_id")
        full_name = request.form.get("full_name")
        class_name = request.form.get("class_name")
        username = request.form.get("username")
        email = request.form.get("email")
        file = request.files.get("file")
        frames = request.files.getlist("frames") or [f for k, f in request.files.items() if k.startswith("frame")]
        
        if not all([full_name, username]) or (file is None and not frames):
            return jsonify({
                "success": False,
                "error": "MISSING_FIELDS",
                "message": "Missing required information"
            }), 400
        
        existing_user = db.get_user(username)
        if existing_user:
            return jsonify({
                "success": False,
                "error": "USERNAME_EXISTS",
                "message": "Username already exists"
            }), 400
        
        try:
            if frames and len(frames) >= 3:
                import requests
                files = []
                for i, f in enumerate(frames[:20]):
                    files.append(("frames", (f"frame{i}.jpg", f.stream.read(), "image/jpeg")))
                data = {"min_liveness": "0.15", "allow_mask": "0"}
                r = requests.post("http://localhost:5000/encode-face", files=files, data=data, timeout=60)
                try:
                    resp = r.json()
                except Exception:
                    return jsonify({"success": False, "error": "ENCODE_ERROR", "message": r.text}), 400
                if not resp.get("success"):
                    return jsonify({"success": False, "error": "ENCODE_ERROR", "message": resp.get("message", "Face encoding failed")}), 400
                emb_base64 = resp.get("embedding")
            else:
                raw_bytes = file.stream.read()
                try:
                    import requests
                    files2 = {"image": ("face.jpg", raw_bytes, "image/jpeg")}
                    data2 = {"min_liveness": "0.15", "allow_mask": "0"}
                    r2 = requests.post("http://localhost:5000/encode-face", files=files2, data=data2, timeout=30)
                    resp2 = r2.json()
                    if not resp2.get("success"):
                        return jsonify({"success": False, "error": "ENCODE_ERROR", "message": resp2.get("message", "Face encoding failed")}), 400
                    emb_base64 = resp2.get("embedding")
                except Exception as e2:
                    return jsonify({"success": False, "error": "ENCODE_ERROR", "message": str(e2)}), 400
            import base64, numpy as np
            emb_live_bytes = base64.b64decode(emb_base64)
            emb_live = np.frombuffer(emb_live_bytes, dtype=np.float32)
            students = db.get_all_students()
            for s in students:
                saved = s.get("embedding")
                if not saved:
                    continue
                if isinstance(saved, list):
                    saved_b64 = base64.b64encode(np.array(saved, dtype=np.float32).tobytes()).decode('utf-8')
                else:
                    saved_b64 = saved
                res = face_auth.compare(saved_b64, emb_base64)
                similarity = res.get("similarity", 0)
                print(f"DEBUG: Comparing with student {s.get('student_id')} - similarity: {similarity}")
                if similarity > 0.75:
                    return jsonify({
                        "success": False,
                        "error": "DUPLICATE_FACE",
                        "message": "You are already a member of this class"
                    }), 400
        except Exception as e:
            err_msg = str(e)
            if "Face mask detected" in err_msg:
                return jsonify({
                    "success": False,
                    "error": "FACE_MASK_DETECTED",
                    "message": err_msg
                }), 400
            return jsonify({
                "success": False,
                "error": "ENCODE_ERROR",
                "message": err_msg
            }), 400
        
        user = UserCreate(
            username=username,
            embedding=emb_base64,
            student_id=student_id,
            full_name=full_name,
            class_name=class_name
        )
        
        user.email = email or username
        user.image_path = f"http://localhost:5002/uploads/faces/{user.email}/face_{user.email}.jpg"
        
        db.save_user(user)
        
        return jsonify({
            "success": True,
            "message": "Student registration successful",
            "student": {
                "student_id": student_id,
                "full_name": full_name,
                "class_name": class_name,
                "username": username
            }
        })
        
    except Exception as e:
        print(f"ERROR /register-student: {str(e)}")
        return jsonify({
            "success": False,
            "error": "REGISTER_ERROR",
            "message": str(e)
        }), 400

@auth_bp.route("/mark-attendance", methods=["POST"])
def mark_attendance():
    """Mark student attendance by face"""
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({
                "success": False,
                "error": "NO_IMAGE",
                "message": "No image provided"
            }), 400
        
        try:
            emb_live_base64 = face_auth.encode(file.stream.read())
        except Exception as e:
            err_msg = str(e)
            if "Face mask detected" in err_msg:
                return jsonify({
                    "success": False,
                    "error": "FACE_MASK_DETECTED",
                    "message": err_msg
                }), 400
            return jsonify({
                "success": False,
                "error": "ENCODE_ERROR",
                "message": err_msg
            }), 400
        
        import base64
        import numpy as np
        emb_live_bytes = base64.b64decode(emb_live_base64)
        emb_live = np.frombuffer(emb_live_bytes, dtype=np.float32)
        
        students = db.get_all_students()
        print(f"DEBUG: Found {len(students)} students")
        
        best_match = None
        best_similarity = 0
        threshold = 0.75
        
        for student in students:
            try:
                saved_emb = student.get("embedding")
                if saved_emb:
                    if isinstance(saved_emb, list):
                        saved_emb_array = np.array(saved_emb, dtype=np.float32)
                        saved_emb_base64 = base64.b64encode(saved_emb_array.tobytes()).decode('utf-8')
                    else:
                        saved_emb_base64 = saved_emb
                    
                    match_result = face_auth.compare(saved_emb_base64, emb_live_base64)
                    similarity = match_result.get("similarity", 0)
                    
                    if similarity > best_similarity and similarity > threshold:
                        best_similarity = similarity
                        best_match = student
            except Exception as e:
                print(f"Error comparing with student {student.get('username', 'unknown')}: {str(e)}")
                continue
        
        if not best_match:
            return jsonify({
                "success": False,
                "error": "NOT_IN_CLASS",
                "message": "You are not in this class"
            }), 400
        
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        attendance_today = db.get_attendance_today()
        print(f"DEBUG: Found {len(attendance_today)} attendance records today")
        print(f"DEBUG: Best match student_id: {best_match.get('student_id')}, username: {best_match.get('username')}")
        
        already_attended = any(
            (att.get("student_id") == best_match.get("student_id")) or 
            (att.get("user_id") == best_match.get("student_id")) or
            (att.get("student_id") == best_match.get("username")) or
            (att.get("user_id") == best_match.get("username"))
            for att in attendance_today
        )
        print(f"DEBUG: Already attended: {already_attended}")
        
        if already_attended:
            return jsonify({
                "success": False,
                "error": "ALREADY_ATTENDED",
                "message": "You have already attended today"
            }), 400
        
        timestamp = datetime.now()
        student_id_to_save = best_match.get("student_id")
        print(f"DEBUG: Saving attendance for student_id: {student_id_to_save}")
        db.save_attendance(student_id_to_save, timestamp)
        print(f"DEBUG: Attendance saved successfully")
        
        return jsonify({
            "success": True,
            "message": "Attendance successful",
            "student": {
                "student_id": best_match.get("student_id"),
                "full_name": best_match.get("full_name"),
                "class_name": best_match.get("class_name"),
                "username": best_match.get("username")
            },
            "timestamp": timestamp.isoformat(),
            "similarity": best_similarity
        })
        
    except Exception as e:
        print(f"ERROR /mark-attendance: {str(e)}")
        return jsonify({
            "success": False,
            "error": "ATTENDANCE_ERROR",
            "message": str(e)
        }), 400


@auth_bp.route("/checkin", methods=["POST"])
def checkin():
    try:
        print("DEBUG: Checkin API called")
        file = request.files.get("file")
        if not file:
            print("DEBUG: No file provided")
            return jsonify({"success": False, "error": "NO_IMAGE", "message": "No image provided"}), 400
        
        print("DEBUG: File received, encoding face...")
        emb_live_base64 = face_auth.encode(file.stream.read())
        import base64, numpy as np
        emb_live_bytes = base64.b64decode(emb_live_base64)
        emb_live = np.frombuffer(emb_live_bytes, dtype=np.float32)
        
        print("DEBUG: Getting students list...")
        students = db.get_all_students()
        print(f"DEBUG: Found {len(students)} students")
        
        best_match, best_similarity = None, 0
        for s in students:
            saved = s.get("embedding")
            if saved:
                if isinstance(saved, list):
                    saved = base64.b64encode(np.array(saved, dtype=np.float32).tobytes()).decode('utf-8')
                res = face_auth.compare(saved, emb_live_base64)
                sim = res.get("similarity", 0)
                print(f"DEBUG: Student {s.get('student_id')} similarity: {sim}")
                if sim > best_similarity and sim > 0.75:
                    best_similarity, best_match = sim, s
        
        if not best_match:
            print("DEBUG: No matching student found")
            return jsonify({"success": False, "error": "NOT_IN_CLASS", "message": "Cannot recognize student"}), 400
        
        print(f"DEBUG: Best match found: {best_match.get('student_id')} with similarity {best_similarity}")
        
        now = datetime.now()
        sid = best_match.get("student_id")
        print(f"DEBUG: Checking attendance status for student {sid}")
        
        has_attendance = db.has_attendance_today(sid)
        print(f"DEBUG: Has attendance today: {has_attendance}")
        
        if has_attendance:
            print("DEBUG: Student already has attendance today")
            return jsonify({"success": False, "error": "ALREADY_ATTENDED", "message": "You have already attended today!"}), 400
        
        print("DEBUG: Saving attendance event...")
        db.save_attendance_event(best_match.get("student_id"), now, "attendance")
        print("DEBUG: Attendance event saved successfully")
        
        return jsonify({"success": True, "student": best_match, "timestamp": now.isoformat(), "similarity": best_similarity})
    except Exception as e:
        print(f"DEBUG: Checkin error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": "CHECKIN_ERROR", "message": str(e)}), 400


@auth_bp.route("/checkout", methods=["POST"])
def checkout():
    try:
        print("DEBUG: Checkout API called")
        file = request.files.get("file")
        if not file:
            print("DEBUG: No file provided for checkout")
            return jsonify({"success": False, "error": "NO_IMAGE", "message": "No image provided"}), 400
        
        print("DEBUG: File received for checkout, encoding face...")
        emb_live_base64 = face_auth.encode(file.stream.read())
        import base64, numpy as np
        emb_live_bytes = base64.b64decode(emb_live_base64)
        emb_live = np.frombuffer(emb_live_bytes, dtype=np.float32)
        
        print("DEBUG: Getting students list for checkout...")
        students = db.get_all_students()
        print(f"DEBUG: Found {len(students)} students for checkout")
        
        best_match, best_similarity = None, 0
        for s in students:
            saved = s.get("embedding")
            if saved:
                if isinstance(saved, list):
                    saved = base64.b64encode(np.array(saved, dtype=np.float32).tobytes()).decode('utf-8')
                res = face_auth.compare(saved, emb_live_base64)
                sim = res.get("similarity", 0)
                print(f"DEBUG: Student {s.get('student_id')} similarity for checkout: {sim}")
                if sim > best_similarity and sim > 0.75:
                    best_similarity, best_match = sim, s
        
        if not best_match:
            print("DEBUG: No matching student found for checkout")
            return jsonify({"success": False, "error": "NOT_IN_CLASS", "message": "Cannot recognize student"}), 400
        
        print(f"DEBUG: Best match found for checkout: {best_match.get('student_id')} with similarity {best_similarity}")
        
        now = datetime.now()
        sid = best_match.get("student_id")
        print(f"DEBUG: Checking if student {sid} has checked in today...")
        
        has_checked_in = db.has_checked_in_today(sid)
        print(f"DEBUG: Has checked in: {has_checked_in}")
        
        if not has_checked_in:
            print("DEBUG: Student has not checked in, cannot checkout")
            return jsonify({"success": False, "error": "CHECKIN_REQUIRED", "message": "You need to Check-in before Check-out."}), 400
        
        print("DEBUG: Saving checkout event...")
        db.save_attendance_event(best_match.get("student_id"), now, "checkout")
        print("DEBUG: Checkout event saved successfully")
        
        return jsonify({"success": True, "student": best_match, "timestamp": now.isoformat(), "similarity": best_similarity})
    except Exception as e:
        print(f"DEBUG: Checkout error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": "CHECKOUT_ERROR", "message": str(e)}), 400


@auth_bp.route("/attendance-summary", methods=["GET"])
def attendance_summary():
    try:
        date_str = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")
        summary = db.summarize_sessions(date_str)
        return jsonify({"success": True, "date": date_str, "summary": summary})
    except Exception as e:
        return jsonify({"success": False, "error": "SUMMARY_ERROR", "message": str(e)}), 400

@auth_bp.route("/stats", methods=["GET"])
def get_stats():
    """Get user statistics (kept for compatibility)"""
    try:
        students = db.get_all_students()
        attendance = db.get_attendance_today()
        
        return jsonify({
            "students": [s.get("username") for s in students],
            "logins": [1] * len(students),
            "total_users": len(students),
            "total_logins": len(attendance)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
=======
from flask import Blueprint, request, jsonify
from ..services.user_service import UserService
from ..utils.validators import validate_register_request
from ..utils.logger import logger
import time

auth_bp = Blueprint("auth", __name__)
user_service = UserService()

@auth_bp.route("/users/register", methods=["POST"])
def register_user():
    # Register new student with basic information and face image
    start_time = time.time()
    
    try:
        # 1. Validate input
        validation_result = validate_register_request(request)
        if not validation_result["valid"]:
            logger.log_request("POST", "/users/register", error=validation_result["message"])
            return jsonify({"success": False, "error": validation_result["message"]}), 400
        
        # 2. Call service
        result = user_service.register_user(
            name=request.form["name"],
            email=request.form["email"],
            image_file=request.files["image"]
        )
        
        response_time = (time.time() - start_time) * 1000
        logger.log_response(
            status_code=201 if result["success"] else 400,
            response_time=response_time,
            user_id=result.get("user_id")
        )
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.log_error(str(e))
        logger.log_response(status_code=500, response_time=response_time)
        return jsonify({"success": False, "error": "Server error"}), 500

@auth_bp.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    # Get student information by ID
    start_time = time.time()
    
    try:
        user = user_service.get_user_by_id(user_id)
        
        response_time = (time.time() - start_time) * 1000
        logger.log_response(status_code=200 if user else 404, response_time=response_time, user_id=user_id)
        
        if user:
            return jsonify({
                "success": True,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "image_path": user.image_path,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat()
                }
            }), 200
        else:
            return jsonify({"success": False, "error": "Student not found"}), 404
            
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.log_error(str(e))
        logger.log_response(status_code=500, response_time=response_time)
        return jsonify({"success": False, "error": "Server error"}), 500

@auth_bp.route("/users/<user_id>/face", methods=["PUT"])
def update_user_face(user_id):
    # Update face image for existing student
    start_time = time.time()
    
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "Missing image file"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No image selected"}), 400
        
        result = user_service.update_user_face(user_id, file)
        
        response_time = (time.time() - start_time) * 1000
        logger.log_response(
            status_code=200 if result["success"] else 400,
            response_time=response_time,
            user_id=user_id
        )
        
        return jsonify(result), 200 if result["success"] else 400
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.log_error(str(e))
        logger.log_response(status_code=500, response_time=response_time)
        return jsonify({"success": False, "error": "Server error"}), 500

@auth_bp.route("/users", methods=["GET"])
def get_all_users():
    # Get list of all students
    start_time = time.time()
    
    try:
        users = user_service.get_all_users()
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "image_path": user.image_path,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            })
        
        response_time = (time.time() - start_time) * 1000
        logger.log_response(status_code=200, response_time=response_time)
        
        return jsonify({
            "success": True,
            "total": len(user_list),
            "users": user_list
        }), 200
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.log_error(str(e))
        logger.log_response(status_code=500, response_time=response_time)
        return jsonify({"success": False, "error": "Server error"}), 500

@auth_bp.route("/users/search", methods=["GET"])
def search_users():
    # Search students by name
    start_time = time.time()
    
    try:
        name = request.args.get('name', '')
        if not name:
            return jsonify({"success": False, "error": "Missing name parameter"}), 400
        
        users = user_service.search_users_by_name(name)
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "image_path": user.image_path,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            })
        
        response_time = (time.time() - start_time) * 1000
        logger.log_response(status_code=200, response_time=response_time)
        
        return jsonify({
            "success": True,
            "total": len(user_list),
            "users": user_list
        }), 200
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.log_error(str(e))
        logger.log_response(status_code=500, response_time=response_time)
        return jsonify({"success": False, "error": "Server error"}), 500
>>>>>>> 3486913fee80855a8b8bce9ab0e74324417a0c27
