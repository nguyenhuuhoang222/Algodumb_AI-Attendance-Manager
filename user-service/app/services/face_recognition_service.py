import requests
import base64
import numpy as np
from typing import Dict, Any, List, Tuple
from ..config.settings import Config
from ..utils.logger import logger

class FaceRecognitionService:
    # Service gọi faceid-service để xử lý nhận dạng khuôn mặt

    def __init__(self):
        self.faceid_url = Config.FACEID_SERVICE_URL
        self.timeout = Config.FACEID_TIMEOUT / 1000  # Convert to seconds
    
    def encode_face(self, image_bytes: bytes) -> Dict[str, Any]:
        # Gọi faceid-service để encode khuôn mặt
        try:
            # 1. Chuẩn bị file upload
            files = {'image': ('face.jpg', image_bytes, 'image/jpeg')}
            
            # 2. Gọi API encode-face
            response = requests.post(
                f"{self.faceid_url}/encode-face",
                files=files,
                timeout=self.timeout
            )
            
            # 3. Xử lý response thành công
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
                        'error': data.get('error', 'Lỗi không xác định')
                    }
            else:
                # 4. Xử lý HTTP error
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.Timeout:
            logger.log_error("FaceID service timeout")
            return {
                'success': False,
                'error': 'FaceID service không phản hồi'
            }
        except requests.exceptions.ConnectionError:
            logger.log_error("FaceID service connection error")
            return {
                'success': False,
                'error': 'Không thể kết nối FaceID service'
            }
        except Exception as e:
            logger.log_error("FaceID service error")
            return {
                'success': False,
                'error': f'Lỗi gọi FaceID service: {str(e)}'
            }
    
    def compare_faces(self, embedding1: str, embedding2: str) -> Dict[str, Any]:
        # So sánh 2 face embeddings
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
                        'error': result.get('error', 'Lỗi so sánh')
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
                'error': f'Lỗi so sánh khuôn mặt: {str(e)}'
            }
    
    def find_matching_users(self, embedding: str, users: List[Dict], threshold: float = None) -> List[Dict]:
        # Tìm users khớp với embedding
        if threshold is None:
            threshold = Config.MATCH_THRESHOLD
        
        matches = []
        
        for user in users:
            if not user.get('face_encoding'):
                continue
                
            # So sánh với embedding của user
            compare_result = self.compare_faces(embedding, user['face_encoding'])
            
            if compare_result['success'] and compare_result['match']:
                matches.append({
                    'user_id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'similarity': compare_result['similarity'],
                    'distance': 1 - compare_result['similarity']
                })
        
        # Sắp xếp theo similarity giảm dần
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        logger.log_face_recognition(
            "find_matches",
            similarity=matches[0]['similarity'] if matches else 0.0
        )
        
        return matches
    
    def health_check(self) -> bool:
        # Kiểm tra faceid-service có hoạt động không
        try:
            response = requests.get(
                f"{self.faceid_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
