from flask import Blueprint, request, jsonify
from ..services.user_service import UserService
from ..utils.validators import validate_register_request
from ..utils.logger import logger
import time

auth_bp = Blueprint("auth", __name__)
user_service = UserService()

@auth_bp.route("/users/register", methods=["POST"])
def register_user():
    # Đăng ký học sinh mới với thông tin cơ bản và ảnh khuôn mặt
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
        return jsonify({"success": False, "error": "Lỗi server"}), 500

@auth_bp.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    # Lấy thông tin học sinh theo ID
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
            return jsonify({"success": False, "error": "Không tìm thấy học sinh"}), 404
            
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.log_error(str(e))
        logger.log_response(status_code=500, response_time=response_time)
        return jsonify({"success": False, "error": "Lỗi server"}), 500

@auth_bp.route("/users/<user_id>/face", methods=["PUT"])
def update_user_face(user_id):
    # Cập nhật ảnh khuôn mặt cho học sinh đã có
    start_time = time.time()
    
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "Thiếu file ảnh"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "Chưa chọn ảnh"}), 400
        
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
        return jsonify({"success": False, "error": "Lỗi server"}), 500

@auth_bp.route("/users", methods=["GET"])
def get_all_users():
    # Lấy danh sách tất cả học sinh
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
        return jsonify({"success": False, "error": "Lỗi server"}), 500

@auth_bp.route("/users/search", methods=["GET"])
def search_users():
    # Tìm kiếm học sinh theo tên
    start_time = time.time()
    
    try:
        name = request.args.get('name', '')
        if not name:
            return jsonify({"success": False, "error": "Thiếu tham số name"}), 400
        
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
        return jsonify({"success": False, "error": "Lỗi server"}), 500
