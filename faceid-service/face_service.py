import cv2
import numpy as np
from PIL import Image
import io
import logging
import base64
from typing import Dict, Tuple, Optional, List
import time

logger = logging.getLogger(__name__)

class FaceService:
    def __init__(self):
        self.cv2 = cv2
        self.recognizer = self._initialize_recognizer()
    
    def _initialize_recognizer(self):
        """Initialize Insightface model"""
        try:
            from insightface.app import FaceAnalysis
            logger.info("Initializing Insightface model...")
            model = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
            model.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("Insightface model initialized successfully")
            return model
        except ImportError:
            raise Exception("Insightface is required. Install with: pip install insightface")
        except Exception as e:
            raise Exception(f"Failed to initialize recognition model: {str(e)}")
    
    def process_image(self, image_bytes):
        """Process uploaded image with enhanced error handling"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Check image properties
            if image.mode not in ['RGB', 'L']:
                image = image.convert('RGB')
            
            # Validate image size
            if image.size[0] < 50 or image.size[1] < 50:
                raise Exception("Image is too small for face detection")
            
            image_array = np.array(image)
            
            # Convert to BGR for OpenCV if needed
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            else:
                image_bgr = image_array
            
            return image_bgr
            
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")
            raise Exception(f"Invalid image format: {str(e)}")
    
    def _check_for_mask(self, image: np.ndarray, face_bbox: List[int]) -> Tuple[bool, float]:
        """Check if the detected face might be wearing a mask - IMPROVED VERSION"""
        try:
            x1, y1, x2, y2 = face_bbox
            face_region = image[y1:y2, x1:x2]
            
            if face_region.size == 0:
                return False, 0.0
            
            height, width = face_region.shape[:2]
            
            # Only check lower part of face for masks
            lower_face = face_region[int(height*0.6):, :]
            
            if lower_face.size == 0:
                return False, 0.0
            
            # Convert to different color spaces for better analysis
            gray_lower = cv2.cvtColor(lower_face, cv2.COLOR_BGR2GRAY)
            hsv_lower = cv2.cvtColor(lower_face, cv2.COLOR_BGR2HSV)
            
            # Calculate multiple features
            features = []
            
            # 1. Color variance (masks often have uniform color)
            color_variance = np.var(lower_face)
            features.append(min(color_variance / 500, 1.0))  # Normalize
            
            # 2. Texture analysis (masks have different texture)
            texture_var = cv2.Laplacian(gray_lower, cv2.CV_64F).var()
            features.append(min((100 - texture_var) / 100, 1.0))  # Lower texture = more likely mask
            
            # 3. Saturation analysis (masks often have low saturation)
            saturation_mean = np.mean(hsv_lower[:,:,1])
            features.append(min((50 - saturation_mean) / 50, 1.0))  # Lower saturation = more likely mask
            
            # 4. Edge density (masks may have fewer edges in mouth area)
            edges = cv2.Canny(gray_lower, 100, 200)
            edge_density = np.sum(edges > 0) / edges.size
            features.append(min((0.1 - edge_density) / 0.1, 1.0))  # Fewer edges = more likely mask
            
            # Weighted average with more weight on texture and edges
            weights = [0.2, 0.4, 0.2, 0.2]  # Texture has highest weight
            mask_confidence = sum(w * f for w, f in zip(weights, features))
            
            # Apply sigmoid-like function to make it less sensitive
            mask_confidence = 1 / (1 + np.exp(-10 * (mask_confidence - 0.5)))
            
            # Only return positive if confidence is high enough
            return mask_confidence > 0.7, float(mask_confidence)
            
        except Exception as e:
            logger.warning(f"Mask detection check failed: {str(e)}")
            return False, 0.0
    
    def extract_face_embedding(self, image_bytes):
        """Extract face embedding using Insightface with IMPROVED mask detection"""
        try:
            # Process image
            image = self.process_image(image_bytes)
            
            # Convert to RGB for Insightface
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect and recognize faces
            faces = self.recognizer.get(rgb_image)
            
            if len(faces) == 0:
                raise Exception("No faces detected in the image")
            
            if len(faces) > 1:
                raise Exception("Multiple faces detected. Please use an image with only one face")
            
            # Get the first face
            face = faces[0]
            bbox = face.bbox.astype(int)
            
            # Check for mask before proceeding - WITH IMPROVED DETECTION
            has_mask, mask_confidence = self._check_for_mask(image, bbox)
            if has_mask:
                # Additional verification: check if face detection score is high
                # Real faces usually have high detection scores, masked faces might have lower
                if face.det_score > 0.8:  # High confidence face detection
                    logger.warning(f"High confidence face detected but mask suspected. Score: {face.det_score}, Mask confidence: {mask_confidence}")
                    # Might be false positive, proceed with caution
                else:
                    raise Exception(f"Face mask detected (confidence: {mask_confidence:.2f}). Please remove mask for recognition.")
            
            # Extract face region for debugging
            x1, y1, x2, y2 = bbox
            face_region = image[y1:y2, x1:x2].copy()
            
            # Convert face region to base64
            _, img_buffer = cv2.imencode('.jpg', face_region)
            face_image_base64 = base64.b64encode(img_buffer).decode('utf-8')
            
            # Convert embedding to base64
            embedding_base64 = base64.b64encode(face.embedding.tobytes()).decode('utf-8')
            
            return embedding_base64, face_image_base64
            
        except Exception as e:
            logger.error(f"Face embedding extraction failed: {str(e)}")
            raise Exception(f"Face embedding extraction failed: {str(e)}")
    
    def compare_embeddings(self, embedding1, embedding2, threshold=0.6):
        """Compare two face embeddings using cosine similarity"""
        try:
            # Normalize embeddings
            embedding1_norm = embedding1 / np.linalg.norm(embedding1)
            embedding2_norm = embedding2 / np.linalg.norm(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1_norm, embedding2_norm)
            
            return similarity > threshold, similarity
        except Exception as e:
            raise Exception(f"Embedding comparison failed: {str(e)}")