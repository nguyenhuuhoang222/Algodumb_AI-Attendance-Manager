import cv2
import numpy as np
from PIL import Image
import io
from typing import Tuple

def resize_image(image_bytes: bytes, max_size: Tuple[int, int] = (640, 480)) -> bytes:
    # Resize image to standard size
    try:
        # 1. Read image from bytes
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert('RGB')
        
        # 2. Resize while maintaining aspect ratio
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 3. Convert to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        return img_byte_arr.getvalue()
    
    except Exception as e:
        raise Exception(f"Image processing error: {str(e)}")

def validate_image_format(image_bytes: bytes) -> bool:
    # Check if image format is valid
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return image.format.lower() in ['jpeg', 'jpg', 'png']
    except:
        return False

def get_image_info(image_bytes: bytes) -> dict:
    # Get image information
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return {
            'format': image.format,
            'size': image.size,
            'mode': image.mode
        }
    except Exception as e:
        raise Exception(f"Error reading image information: {str(e)}")
