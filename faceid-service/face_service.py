import cv2
import numpy as np
from PIL import Image
import io
import logging
import base64

logger = logging.getLogger(__name__)

class FaceService:
    def __init__(self):
        self.cv2 = cv2
        self.recognizer = self._initialize_recognizer()
    
    def _initialize_recognizer(self):
        """Initialize Insightface model"""
        try:
            from insightface.app import FaceAnalysis
            model = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
            model.prepare(ctx_id=0, det_size=(640, 640))
            return model
        except ImportError:
            raise Exception("Insightface is required. Install with: pip install insightface")
        except Exception as e:
            raise Exception(f"Failed to initialize recognition model: {str(e)}")
    
    def process_image(self, image_bytes):
        """Process uploaded image"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image = image.convert('RGB')
            image_array = np.array(image)
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            return image_bgr
        except Exception as e:
            raise Exception(f"Image processing failed: {str(e)}")
    
    def extract_face_embedding(self, image_bytes):
        """Extract face embedding using Insightface"""
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
            
            # Extract face region for debugging
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            face_region = image[y1:y2, x1:x2].copy()
            
            # Convert face region to base64
            _, img_buffer = cv2.imencode('.jpg', face_region)
            face_image_base64 = base64.b64encode(img_buffer).decode('utf-8')
            
            # Convert embedding to base64
            embedding_base64 = base64.b64encode(face.embedding.tobytes()).decode('utf-8')
            
            return embedding_base64, face_image_base64
            
        except Exception as e:
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