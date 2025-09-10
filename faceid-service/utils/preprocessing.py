# Tiền xử lý và đọc ảnh
import numpy as np
import cv2
from typing import Optional

def read_image_bytes(b: bytes) -> Optional[np.ndarray]:
    arr = np.frombuffer(b, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img
