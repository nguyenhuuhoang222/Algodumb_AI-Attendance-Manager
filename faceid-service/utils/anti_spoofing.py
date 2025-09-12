import cv2
import numpy as np
from typing import Dict, Tuple, List
import logging
from deepface import DeepFace

logger = logging.getLogger(__name__)

class AntiSpoofing:
    def __init__(self):
        """Initialize DeepFace anti-spoofing"""
        logger.info("Initializing DeepFace anti-spoofing...")
    
    def check_spoof(self, image: np.ndarray, face_bbox: List[int]) -> Tuple[bool, float]:
        """
        Check if face is real or spoof using DeepFace
        Returns: (is_real, confidence)
        """
        try:
            x1, y1, x2, y2 = face_bbox
            face_region = image[y1:y2, x1:x2]
            
            if face_region.size == 0:
                return False, 0.0
            
            # Convert to RGB for DeepFace
            face_rgb = cv2.cvtColor(face_region, cv2.COLOR_BGR2RGB)
            
            # Use DeepFace for spoof detection
            result = DeepFace.analyze(
                img_path=face_rgb,
                actions=['spoof'],
                detector_backend='skip',  # We already have the face region
                enforce_detection=False,
                silent=True
            )
            
            # Extract spoof score (0=real, 1=spoof)
            if isinstance(result, list):
                spoof_score = result[0]['spoof']
            else:
                spoof_score = result['spoof']
            
            # Convert to real confidence
            real_confidence = 1.0 - spoof_score
            is_real = real_confidence > 0.7  # Adjust threshold as needed
            
            return is_real, float(real_confidence)
            
        except Exception as e:
            logger.error(f"DeepFace anti-spoofing failed: {str(e)}")
            # Fallback to basic spoof detection
            return self._basic_spoof_check(image, face_bbox)
    
    def _basic_spoof_check(self, image: np.ndarray, face_bbox: List[int]) -> Tuple[bool, float]:
        """
        Basic spoof detection using image quality metrics
        Fallback method when DeepFace fails
        """
        try:
            x1, y1, x2, y2 = face_bbox
            face_region = image[y1:y2, x1:x2]
            
            if face_region.size == 0:
                return False, 0.0
            
            # Check image quality indicators
            quality_score = self._calculate_image_quality(face_region)
            
            # Lower quality might indicate spoof (photo, screen, etc.)
            is_real = quality_score > 0.6  # Adjust threshold
            
            return is_real, float(quality_score)
            
        except Exception as e:
            logger.warning(f"Basic spoof check failed: {str(e)}")
            return True, 0.5  # Default to real if check fails
    
    def _calculate_image_quality(self, image: np.ndarray) -> float:
        """Calculate image quality score"""
        # 1. Check blurriness
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_score = min(blur / 500, 1.0)  # Normalize
        
        # 2. Check contrast
        contrast = np.std(gray)
        contrast_score = min(contrast / 100, 1.0)  # Normalize
        
        # 3. Check brightness
        brightness = np.mean(gray)
        brightness_score = 1.0 - abs(brightness - 127) / 127  # Closer to 127 is better
        
        return (blur_score + contrast_score + brightness_score) / 3

# Global instance
anti_spoofing = AntiSpoofing()