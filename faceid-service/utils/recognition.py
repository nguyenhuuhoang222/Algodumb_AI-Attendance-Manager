<<<<<<< HEAD
# Placeholder cho nhận dạng dùng model thật (ArcFace/FaceNet)
# Thay thế _dummy_embed trong face_api bằng hàm gọi model tại đây.
=======
import numpy as np
import base64
import logging

logger = logging.getLogger(__name__)

class FaceRecognizer:
    @staticmethod
    def compare_embeddings(embedding1, embedding2, threshold=None):
        """
        Compare two embeddings using cosine similarity
        Returns: (is_match, similarity_score)
        """
        try:
            # Use default threshold if not provided
            if threshold is None:
                from thresholds_config import FACE_SIMILARITY_THRESHOLD
                threshold = FACE_SIMILARITY_THRESHOLD
                
            # Normalize embeddings
            norm1 = embedding1 / np.linalg.norm(embedding1)
            norm2 = embedding2 / np.linalg.norm(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(norm1, norm2)
            
            return similarity > threshold, similarity
        except Exception as e:
            logger.error(f"Error in embedding comparison: {str(e)}")
            return False, 0.0
    
    @staticmethod
    def embedding_to_base64(embedding):
        """Convert numpy array to base64 string"""
        return base64.b64encode(embedding.tobytes()).decode('utf-8')
    
    @staticmethod
    def base64_to_embedding(base64_str):
        """Convert base64 string back to numpy array"""
        bytes_data = base64.b64decode(base64_str)
        return np.frombuffer(bytes_data, dtype=np.float32)
>>>>>>> clean-branch
