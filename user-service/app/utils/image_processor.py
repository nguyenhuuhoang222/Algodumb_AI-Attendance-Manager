import cv2
import numpy as np
from PIL import Image
import io
from typing import Tuple

def resize_image(image_bytes: bytes, max_size: Tuple[int, int] = (640, 480)) -> bytes:
    # Resize ảnh về kích thước chuẩn
    try:
        # 1. Đọc ảnh từ bytes
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert('RGB')
        
        # 2. Resize với tỷ lệ giữ nguyên
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 3. Chuyển về bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        return img_byte_arr.getvalue()
    
    except Exception as e:
        raise Exception(f"Lỗi xử lý ảnh: {str(e)}")

def validate_image_format(image_bytes: bytes) -> bool:
    # Kiểm tra định dạng ảnh có hợp lệ không
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return image.format.lower() in ['jpeg', 'jpg', 'png']
    except:
        return False

def get_image_info(image_bytes: bytes) -> dict:
    # Lấy thông tin ảnh
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return {
            'format': image.format,
            'size': image.size,
            'mode': image.mode
        }
    except Exception as e:
        raise Exception(f"Lỗi đọc thông tin ảnh: {str(e)}")
