from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import base64
import numpy as np
from face_service import FaceService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize service
face_service = FaceService()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "service": "FaceID Service",
        "version": "1.0.0"
    })

@app.route('/encode-face', methods=['POST'])
def encode_face():
    try:
        if 'image' not in request.files:
            return jsonify({
                "success": False,
                "error": "NO_IMAGE_PROVIDED",
                "message": "No image provided"
            }), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({
                "success": False,
                "error": "EMPTY_FILE", 
                "message": "No image selected"
            }), 400
        
        # Read and validate image
        image_bytes = image_file.read()
        if len(image_bytes) == 0:
            return jsonify({
                "success": False,
                "error": "EMPTY_IMAGE",
                "message": "Empty image file"
            }), 400
        
        if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
            return jsonify({
                "success": False,
                "error": "FILE_TOO_LARGE",
                "message": "Image file too large (max 10MB)"
            }), 400
        
        # Extract embedding
        embedding, face_image = face_service.extract_face_embedding(image_bytes)
        
        return jsonify({
            "success": True,
            "embedding": embedding,
            "face_image": face_image,
            "message": "Face encoded successfully"
        })
        
    except Exception as e:
        logger.error(f"Error in encode_face: {str(e)}")
        error_message = str(e)
        
        # Categorize errors for better client handling
        if "mask detected" in error_message.lower():
            error_code = "FACE_MASK_DETECTED"
        elif "no faces detected" in error_message.lower():
            error_code = "NO_FACE_DETECTED"
        elif "multiple faces" in error_message.lower():
            error_code = "MULTIPLE_FACES"
        elif "image processing" in error_message.lower():
            error_code = "IMAGE_PROCESSING_ERROR"
        else:
            error_code = "EXTRACTION_ERROR"
        
        return jsonify({
            "success": False,
            "error": error_code,
            "message": error_message
        }), 400

@app.route('/compare-faces', methods=['POST'])
def compare_faces():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "INVALID_JSON",
                "message": "Invalid JSON data"
            }), 400
        
        if 'embedding1' not in data or 'embedding2' not in data:
            return jsonify({
                "success": False,
                "error": "MISSING_EMBEDDINGS",
                "message": "Missing embeddings in request data"
            }), 400
        
        # Get optional threshold from request
        threshold = float(data.get('threshold', 0.6))
        
        # Convert base64 to numpy arrays
        embedding1 = np.frombuffer(base64.b64decode(data['embedding1']), dtype=np.float32)
        embedding2 = np.frombuffer(base64.b64decode(data['embedding2']), dtype=np.float32)
        
        # Compare embeddings
        is_match, similarity = face_service.compare_embeddings(embedding1, embedding2, threshold)
        
        response_data = {
            "success": True,
            "match": bool(is_match),
            "similarity": float(similarity),
            "threshold": float(threshold)
        }
        
        # Add debug info if available and faces don't match
        if not is_match and 'image1_base64' in data and 'image2_base64' in data:
            try:
                # Remove data URI prefix if present
                img1_data = data['image1_base64'].split(',')[-1]
                img2_data = data['image2_base64'].split(',')[-1]
                
                img1_bytes = base64.b64decode(img1_data)
                img2_bytes = base64.b64decode(img2_data)
                
                _, face_region1 = face_service.extract_face_embedding(img1_bytes)
                _, face_region2 = face_service.extract_face_embedding(img2_bytes)
                
                response_data["debug"] = {
                    "face1_image": face_region1,
                    "face2_image": face_region2,
                    "message": "Faces do not match. See extracted face regions."
                }
            except Exception as debug_error:
                logger.warning(f"Debug image processing failed: {str(debug_error)}")
                response_data["debug_error"] = str(debug_error)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in compare_faces: {str(e)}")
        return jsonify({
            "success": False,
            "error": "COMPARISON_ERROR",
            "message": f"Face comparison failed: {str(e)}"
        }), 400

@app.route('/verify-liveness', methods=['POST'])
def verify_liveness():
    """Endpoint specifically for liveness detection"""
    try:
        if 'image' not in request.files:
            return jsonify({
                "success": False,
                "error": "NO_IMAGE_PROVIDED",
                "message": "No image provided"
            }), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({
                "success": False,
                "error": "EMPTY_FILE", 
                "message": "No image selected"
            }), 400
        
        # Read and validate image
        image_bytes = image_file.read()
        if len(image_bytes) == 0:
            return jsonify({
                "success": False,
                "error": "EMPTY_IMAGE",
                "message": "Empty image file"
            }), 400
        
        # Process image
        image = face_service.process_image(image_bytes)
        
        # Convert to RGB for Insightface
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        faces = face_service.recognizer.get(rgb_image)
        
        if len(faces) == 0:
            return jsonify({
                "success": False,
                "error": "NO_FACE_DETECTED",
                "message": "No faces detected in the image"
            }), 400
        
        if len(faces) > 1:
            return jsonify({
                "success": False,
                "error": "MULTIPLE_FACES",
                "message": "Multiple faces detected. Please use an image with only one face"
            }), 400
        
        # Get the first face
        face = faces[0]
        bbox = face.bbox.astype(int)
        
        # Check for mask
        has_mask, mask_confidence = face_service._check_for_mask(image, bbox)
        
        # Check for spoofing
        is_real, spoof_confidence = face_service._check_for_spoof(image, bbox)
        
        return jsonify({
            "success": True,
            "mask_detected": has_mask,
            "mask_confidence": mask_confidence,
            "is_real": is_real,
            "spoof_confidence": spoof_confidence,
            "message": "Liveness verification completed"
        })
        
    except Exception as e:
        logger.error(f"Error in verify_liveness: {str(e)}")
        return jsonify({
            "success": False,
            "error": "LIVENESS_VERIFICATION_ERROR",
            "message": f"Liveness verification failed: {str(e)}"
        }), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "ENDPOINT_NOT_FOUND",
        "message": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "INTERNAL_SERVER_ERROR",
        "message": "Internal server error"
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)