import cv2
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class MaskDetector:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def detect_mask(self, image: np.ndarray, face_bbox: List[int]) -> Dict:
        """
        Detect if a face is wearing a mask
        Returns detailed mask detection results
        """
        try:
            x1, y1, x2, y2 = face_bbox
            face_region = image[y1:y2, x1:x2]
            
            if face_region.size == 0:
                return {
                    "mask_detected": False,
                    "confidence": 0.0,
                    "error": "Empty face region"
                }
            
            # Convert to grayscale for analysis
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Analyze face region for mask indicators
            mask_confidence = self._analyze_mask_indicators(face_region, gray_face)
            
            return {
                "mask_detected": mask_confidence > 0.4,  # Lowered from 0.6 to 0.4 to detect easier
                "confidence": float(mask_confidence),
                "bbox": face_bbox,
                "region_size": f"{face_region.shape[1]}x{face_region.shape[0]}"
            }
            
        except Exception as e:
            logger.error(f"Mask detection error: {str(e)}")
            return {
                "mask_detected": False,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _analyze_mask_indicators(self, face_region: np.ndarray, gray_face: np.ndarray) -> float:
        """Analyze multiple indicators for mask presence"""
        indicators = []
        
        # 1. Check for mouth area obscurity
        mouth_obscurity = self._check_mouth_obscurity(face_region)
        indicators.append(mouth_obscurity)
        
        # 2. Check color distribution in lower face
        color_consistency = self._check_color_consistency(face_region)
        indicators.append(color_consistency)
        
        # 3. Check texture patterns
        texture_analysis = self._analyze_texture(gray_face)
        indicators.append(texture_analysis)
        
        # 4. Check edge density (masks often have different edge patterns)
        edge_density = self._check_edge_density(gray_face)
        indicators.append(edge_density)
        
        return sum(indicators) / len(indicators)
    
    def _check_mouth_obscurity(self, face_region: np.ndarray) -> float:
        """Check if mouth area appears obscured"""
        height, width = face_region.shape[:2]
        mouth_region = face_region[int(height*0.6):int(height*0.9), 
                                  int(width*0.25):int(width*0.75)]
        
        if mouth_region.size == 0:
            return 0.8
        
        # Calculate color variance in mouth region
        color_variance = np.var(mouth_region)
        return min(color_variance / 1000, 1.0)  # Normalize
    
    def _check_color_consistency(self, face_region: np.ndarray) -> float:
        """Check color consistency which might indicate mask"""
        # Split into upper and lower parts
        height = face_region.shape[0]
        upper_face = face_region[:height//2, :]
        lower_face = face_region[height//2:, :]
        
        if upper_face.size == 0 or lower_face.size == 0:
            return 0.5
        
        # Compare color means
        upper_mean = np.mean(upper_face)
        lower_mean = np.mean(lower_face)
        
        color_diff = abs(upper_mean - lower_mean)
        return min(color_diff / 50, 1.0)  # Higher difference suggests mask
    
    def _analyze_texture(self, gray_face: np.ndarray) -> float:
        """Analyze texture patterns"""
        # Calculate LBP-like texture variance
        if gray_face.size == 0:
            return 0.5
        
        blur = cv2.Laplacian(gray_face, cv2.CV_64F).var()
        return 0.7 if blur < 100 else 0.3  # Lower blur might indicate mask
    
    def _check_edge_density(self, gray_face: np.ndarray) -> float:
        """Check edge density patterns"""
        if gray_face.size == 0:
            return 0.5
        
        edges = cv2.Canny(gray_face, 100, 200)
        edge_density = np.sum(edges > 0) / edges.size
        return 0.7 if edge_density < 0.1 else 0.3

# Global instance
mask_detector = MaskDetector()