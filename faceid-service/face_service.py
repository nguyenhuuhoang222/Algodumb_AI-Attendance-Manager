import cv2
import numpy as np
from PIL import Image
import io
import logging
import base64
from typing import Dict, Tuple, Optional, List
import time

# Import new modules
from utils.mask_detector import mask_detector
from utils.anti_spoofing import anti_spoofing

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
        """Use the dedicated mask detector"""
        try:
            result = mask_detector.detect_mask(image, face_bbox)
            return result["mask_detected"], result["confidence"]
        except Exception as e:
            logger.warning(f"Mask detection failed: {str(e)}")
            return False, 0.0
    
    def _check_for_spoof(self, image: np.ndarray, face_bbox: List[int]) -> Tuple[bool, float]:
        """Check if face is real or spoofed using DeepFace"""
        try:
            is_real, confidence = anti_spoofing.check_spoof(image, face_bbox)
            return is_real, confidence
        except Exception as e:
            logger.warning(f"Spoof detection failed: {str(e)}")
            return True, 0.5  # Default to real if check fails
    
    def extract_face_embedding(self, image_bytes):
        """Extract face embedding with mask and spoof detection"""
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
            
            # Check for mask
            has_mask, mask_confidence = self._check_for_mask(image, bbox)
            if has_mask:
                raise Exception(f"Face mask detected (confidence: {mask_confidence:.2f}). Please remove mask for recognition.")
            
            # Check for spoofing
            is_real, spoof_confidence = self._check_for_spoof(image, bbox)
            if not is_real:
                raise Exception(f"Possible spoof attack detected (confidence: {spoof_confidence:.2f}). Please use a real face.")
            
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