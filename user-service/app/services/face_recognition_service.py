import requests
import base64
import numpy as np
from typing import Dict, Any, List, Tuple
from ..config.settings import Config
from ..utils.logger import logger

class FaceRecognitionService:
    # Service calling faceid-service to handle face recognition

    def __init__(self):
        self.faceid_url = Config.FACEID_SERVICE_URL
        self.timeout = Config.FACEID_TIMEOUT / 1000  # Convert to seconds
    
    def encode_face(self, image_bytes: bytes) -> Dict[str, Any]:
        # Call faceid-service to encode face
        try:
            # 1. Prepare file upload
            files = {'image': ('face.jpg', image_bytes, 'image/jpeg')}
            
            # 2. Call API encode-face
            response = requests.post(
                f"{self.faceid_url}/encode-face",
                files=files,
                timeout=self.timeout
            )
            
            # 3. Process successful response
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return {
                        'success': True,
                        'embedding': data.get('embedding'),
                        'face_image': data.get('face_image'),
                        'message': data.get('message')
                    }
                else:
                    return {
                        'success': False,
                        'error': data.get('error', 'Unknown error')
                    }
            else:
                # 4. Handle HTTP error
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.Timeout:
            logger.log_error("FaceID service timeout")
            return {
                'success': False,
                'error': 'FaceID service not responding'
            }
        except requests.exceptions.ConnectionError:
            logger.log_error("FaceID service connection error")
            return {
                'success': False,
                'error': 'Cannot connect to FaceID service'
            }
        except Exception as e:
            logger.log_error("FaceID service error")
            return {
                'success': False,
                'error': f'Error calling FaceID service: {str(e)}'
            }
    
    def compare_faces(self, embedding1: str, embedding2: str) -> Dict[str, Any]:
        # Compare 2 face embeddings
        try:
            data = {
                'embedding1': embedding1,
                'embedding2': embedding2
            }
            
            response = requests.post(
                f"{self.faceid_url}/compare-faces",
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return {
                        'success': True,
                        'match': result.get('match', False),
                        'similarity': result.get('similarity', 0.0),
                        'threshold': result.get('threshold', 0.6)
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', 'Comparison error')
                    }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.log_error("Face comparison error")
            return {
                'success': False,
                'error': f'Face comparison error: {str(e)}'
            }
    
    def find_matching_users(self, embedding: str, users: List[Dict], threshold: float = None) -> List[Dict]:
        # Find users matching embedding
        if threshold is None:
            threshold = Config.MATCH_THRESHOLD
        
        matches = []
        
        for user in users:
            if not user.get('face_encoding'):
                continue
                
            # Compare with user's embedding
            compare_result = self.compare_faces(embedding, user['face_encoding'])
            
            if compare_result['success'] and compare_result['match']:
                matches.append({
                    'user_id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'similarity': compare_result['similarity'],
                    'distance': 1 - compare_result['similarity']
                })
        
        # Sort by similarity descending
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        logger.log_face_recognition(
            "find_matches",
            similarity=matches[0]['similarity'] if matches else 0.0
        )
        
        return matches
    
    def health_check(self) -> bool:
        # Check if faceid-service is working
        try:
            response = requests.get(
                f"{self.faceid_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
