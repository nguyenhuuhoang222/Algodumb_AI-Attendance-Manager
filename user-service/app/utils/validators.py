from flask import request
from typing import Dict, Any
import re

def validate_register_request(req) -> Dict[str, Any]:
    # Validate request đăng ký học sinh
    # 1. Kiểm tra tên học sinh
    if 'name' not in req.form or not req.form['name'].strip():
        return {"valid": False, "message": "Tên học sinh là bắt buộc"}
    
    # 2. Kiểm tra email/mã học sinh
    if 'email' not in req.form or not req.form['email'].strip():
        return {"valid": False, "message": "Email hoặc mã học sinh là bắt buộc"}
    
    # 3. Kiểm tra file ảnh
    if 'image' not in req.files:
        return {"valid": False, "message": "Ảnh khuôn mặt là bắt buộc"}
    
    file = req.files['image']
    if file.filename == '':
        return {"valid": False, "message": "Chưa chọn ảnh"}
    
    # 4. Validate email format
    email = req.form['email'].strip()
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) and not email.isalnum():
        return {"valid": False, "message": "Email hoặc mã học sinh không hợp lệ"}
    
    return {"valid": True}

def validate_attendance_request(req) -> Dict[str, Any]:
    # Validate request điểm danh
    if 'image' not in req.files:
        return {"valid": False, "message": "Ảnh là bắt buộc"}
    
    file = req.files['image']
    if file.filename == '':
        return {"valid": False, "message": "Chưa chọn ảnh"}
    
    return {"valid": True}

def validate_image_size(file, max_size: int = 5242880) -> Dict[str, Any]:
    # Validate kích thước ảnh
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        return {"valid": False, "message": f"Ảnh quá lớn. Tối đa {max_size // 1024 // 1024}MB"}
    
    return {"valid": True}
