from flask import request
from typing import Dict, Any
import re

def validate_register_request(req) -> Dict[str, Any]:
    # Validate student registration request
    # 1. Check student name
    if 'name' not in req.form or not req.form['name'].strip():
        return {"valid": False, "message": "Student name is required"}
    
    # 2. Check email/student ID
    if 'email' not in req.form or not req.form['email'].strip():
        return {"valid": False, "message": "Email or student ID is required"}
    
    # 3. Check image file
    if 'image' not in req.files:
        return {"valid": False, "message": "Face image is required"}
    
    file = req.files['image']
    if file.filename == '':
        return {"valid": False, "message": "No image selected"}
    
    # 4. Validate email format
    email = req.form['email'].strip()
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) and not email.isalnum():
        return {"valid": False, "message": "Invalid email or student ID"}
    
    return {"valid": True}

def validate_attendance_request(req) -> Dict[str, Any]:
    # Validate attendance request
    if 'image' not in req.files:
        return {"valid": False, "message": "Image is required"}
    
    file = req.files['image']
    if file.filename == '':
        return {"valid": False, "message": "No image selected"}
    
    return {"valid": True}

def validate_image_size(file, max_size: int = 5242880) -> Dict[str, Any]:
    # Validate image size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        return {"valid": False, "message": f"Image too large. Maximum {max_size // 1024 // 1024}MB"}
    
    return {"valid": True}
