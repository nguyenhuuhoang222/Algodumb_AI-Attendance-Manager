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
        # Accept either single image or sequence of frames: 'frames' list or keys starting with 'frame'
        frames = request.files.getlist('frames')
        if not frames:
            # collect frame0, frame1,... style
            frames = [f for key, f in request.files.items() if key.startswith('frame')]

        if frames and len(frames) >= 3:
            # sequence mode
            frame_bytes = []
            total_size = 0
            for f in frames:
                b = f.read()
                if not b:
                    continue
                total_size += len(b)
                if total_size > 20 * 1024 * 1024:
                    return jsonify({
                        "success": False,
                        "error": "FILE_TOO_LARGE",
                        "message": "Total frames size too large (max 20MB)"
                    }), 400
                frame_bytes.append(b)
            # optional per-request liveness threshold override
            min_liveness = request.form.get('min_liveness') or request.args.get('min_liveness')
            allow_mask = request.form.get('allow_mask') or request.args.get('allow_mask')
            min_live_val = float(min_liveness) if min_liveness is not None else None
            embedding, face_image, scores = face_service.extract_embedding_from_sequence(frame_bytes, min_live_val, bool(allow_mask) and str(allow_mask).lower() not in ['0','false','no'])
            return jsonify({
                "success": True,
                "embedding": embedding,
                "face_image": face_image,
                "temporal_scores": scores,
                "message": "Face encoded successfully (sequence)"
            })
        # single image mode
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
        image_bytes = image_file.read()
        if len(image_bytes) == 0:
            return jsonify({
                "success": False,
                "error": "EMPTY_IMAGE",
                "message": "Empty image file"
            }), 400
        if len(image_bytes) > 10 * 1024 * 1024:
            return jsonify({
                "success": False,
                "error": "FILE_TOO_LARGE",
                "message": "Image file too large (max 10MB)"
            }), 400
        # optional per-request liveness threshold override
        min_liveness = request.form.get('min_liveness') or request.args.get('min_liveness')
        allow_mask = request.form.get('allow_mask') or request.args.get('allow_mask')
        min_live_val = float(min_liveness) if min_liveness is not None else None
        embedding, face_image = face_service.extract_face_embedding(image_bytes, min_live_val, bool(allow_mask) and str(allow_mask).lower() not in ['0','false','no'])
        
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
        
        # Get optional threshold from request - Tăng ngưỡng để kiểm tra trùng mặt chặt chẽ hơn
        from thresholds_config import FACE_SIMILARITY_THRESHOLD
        threshold = float(data.get('threshold', FACE_SIMILARITY_THRESHOLD))
        
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