from flask import Blueprint, request, jsonify
from ..services.attendance_service import AttendanceService
from ..utils.validators import validate_attendance_request
from ..utils.logger import logger
import time

attendance_bp = Blueprint("attendance", __name__)
attendance_service = AttendanceService()

@attendance_bp.route("/attendance/mark", methods=["POST"])
def mark_attendance():
    """Điểm danh cho 1 khuôn mặt"""
    start_time = time.time()
    
    try:
        # Validate input
        validation_result = validate_attendance_request(request)
        if not validation_result["valid"]:
            logger.log_request("POST", "/attendance/mark", error=validation_result["message"])
            return jsonify({"success": False, "error": validation_result["message"]}), 400
        
        # Get optional parameters
        user_id = request.form.get('user_id')
        note = request.form.get('note')
        
        # Call service
        result = attendance_service.mark_attendance_single(
            image_file=request.files["image"],
            user_id=user_id,
            note=note
        )
        
        response_time = (time.time() - start_time) * 1000
        logger.log_response(
            status_code=200 if result["success"] else 400,
            response_time=response_time,
            user_id=result.get("user_id")
        )
        
        return jsonify(result), 200 if result["success"] else 400
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.log_error(str(e))
        logger.log_response(status_code=500, response_time=response_time)
        return jsonify({"success": False, "error": "Lỗi server"}), 500

@attendance_bp.route("/attendance/mark-multi", methods=["POST"])
def mark_attendance_multi():
    #
    start_time = time.time()
    
    try:
        # 1. Validate input
        validation_result = validate_attendance_request(request)
        if not validation_result["valid"]:
            logger.log_request("POST", "/attendance/mark-multi", error=validation_result["message"])
            return jsonify({"success": False, "error": validation_result["message"]}), 400
        
        # 2. Get optional parameters
        note = request.form.get('note')
        class_id = request.form.get('classId')  # Hỗ trợ classId
        
        # 3. Call service
        result = attendance_service.mark_attendance_multi(
            image_file=request.files["image"],
            note=note,
            class_id=class_id
        )
        
        response_time = (time.time() - start_time) * 1000
        logger.log_response(
            status_code=200 if result["success"] else 400,
            response_time=response_time
        )
        
        return jsonify(result), 200 if result["success"] else 400
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.log_error(str(e))
        logger.log_response(status_code=500, response_time=response_time)
        return jsonify({"success": False, "error": "Lỗi server"}), 500

@attendance_bp.route("/attendance/daily", methods=["GET"])
def get_daily_attendance():
    # Lấy danh sách điểm danh theo ngày
    start_time = time.time()
    
    try:
        attendance_date = request.args.get('date')
        if not attendance_date:
            return jsonify({"success": False, "error": "Thiếu tham số date"}), 400
        
        limit = int(request.args.get('limit', 100))
        class_id = request.args.get('classId')  # Hỗ trợ classId
        
        result = attendance_service.get_daily_attendance(attendance_date, limit, class_id)
        
        response_time = (time.time() - start_time) * 1000
        logger.log_response(
            status_code=200 if result["success"] else 400,
            response_time=response_time
        )
        
        return jsonify(result), 200 if result["success"] else 400
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.log_error(str(e))
        logger.log_response(status_code=500, response_time=response_time)
        return jsonify({"success": False, "error": "Lỗi server"}), 500

@attendance_bp.route("/attendance/user/<user_id>", methods=["GET"])
def get_user_attendance_history(user_id):
    # Lấy lịch sử điểm danh của học sinh
    start_time = time.time()
    
    try:
        limit = int(request.args.get('limit', 50))
        
        result = attendance_service.get_user_attendance_history(user_id, limit)
        
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

@attendance_bp.route("/attendance/absent-batch", methods=["POST"])
def mark_absent_batch():
    # Đánh dấu vắng hàng loạt
    start_time = time.time()
    
    try:
        data = request.get_json()
        if not data or 'user_ids' not in data or 'date' not in data:
            return jsonify({"success": False, "error": "Thiếu user_ids hoặc date"}), 400
        
        user_ids = data['user_ids']
        attendance_date = data['date']
        
        if not isinstance(user_ids, list) or len(user_ids) == 0:
            return jsonify({"success": False, "error": "user_ids phải là danh sách không rỗng"}), 400
        
        result = attendance_service.mark_absent_batch(user_ids, attendance_date)
        
        response_time = (time.time() - start_time) * 1000
        logger.log_response(
            status_code=200 if result["success"] else 400,
            response_time=response_time
        )
        
        return jsonify(result), 200 if result["success"] else 400
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.log_error(str(e))
        logger.log_response(status_code=500, response_time=response_time)
        return jsonify({"success": False, "error": "Lỗi server"}), 500

@attendance_bp.route("/attendance/stats", methods=["GET"])
def get_attendance_stats():
    # Lấy thống kê điểm danh
    start_time = time.time()
    
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({"success": False, "error": "Thiếu start_date hoặc end_date"}), 400
        
        # This would need to be implemented in AttendanceService
        # For now, return a placeholder
        result = {
            "success": True,
            "start_date": start_date,
            "end_date": end_date,
            "stats": {
                "total_records": 0,
                "present_count": 0,
                "absent_count": 0,
                "unique_users": 0
            }
        }
        
        response_time = (time.time() - start_time) * 1000
        logger.log_response(status_code=200, response_time=response_time)
        
        return jsonify(result), 200
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.log_error(str(e))
        logger.log_response(status_code=500, response_time=response_time)
        return jsonify({"success": False, "error": "Lỗi server"}), 500
