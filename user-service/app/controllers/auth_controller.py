# Đăng ký/đăng nhập bằng khuôn mặt
from flask import Blueprint, request, jsonify
from ..services.face_auth_service import FaceAuthService
from ..services.firebase_service import FirebaseService
from ..models.user_models import UserCreate, LoginResult

auth_bp = Blueprint("auth", __name__)
face_auth = FaceAuthService(base_url="http://localhost:5001/api")
db = FirebaseService()  # Đọc config từ biến môi trường

@auth_bp.route("/register-face", methods=["POST"])
def register_face():
    # form-data: file=...
    file = request.files.get("file")
    username = request.form.get("username")
    if not file or not username:
        return jsonify({"error":"Thiếu file hoặc username"}), 400

    emb = face_auth.encode(file.stream.read())
    user = UserCreate(username=username, embedding=emb)
    # Lưu Firestore: users/{username}
    db.save_user(user)
    return jsonify({"ok": True})

@auth_bp.route("/login-face", methods=["POST"])
def login_face():
    # form-data: file=...
    file = request.files.get("file")
    username = request.form.get("username")
    if not file or not username:
        return jsonify({"error":"Thiếu file hoặc username"}), 400

    # Lấy embedding người dùng đã lưu
    saved = db.get_user(username)
    if not saved:
        return jsonify({"error":"User không tồn tại"}), 404

    emb_live = face_auth.encode(file.stream.read())
    match = face_auth.compare(saved["embedding"], emb_live)
    res = LoginResult(username=username, match=match["match"], distance=match["distance"])
    return jsonify(res.model_dump())
