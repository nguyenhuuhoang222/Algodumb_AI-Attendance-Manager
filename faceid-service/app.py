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
    return jsonify({"status": "healthy", "service": "FaceID Service"})

@app.route('/encode-face', methods=['POST'])
def encode_face():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({"error": "No image selected"}), 400
        
        # Extract embedding
        embedding, face_image = face_service.extract_face_embedding(image_file.read())
        
        return jsonify({
            "success": True,
            "embedding": embedding,
            "face_image": face_image,
            "message": "Face encoded successfully"
        })
        
    except Exception as e:
        logger.error(f"Error in encode_face: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/compare-faces', methods=['POST'])
def compare_faces():
    try:
        data = request.get_json()
        if not data or 'embedding1' not in data or 'embedding2' not in data:
            return jsonify({"error": "Missing embeddings"}), 400
        
        # Convert base64 to numpy arrays
        embedding1 = np.frombuffer(base64.b64decode(data['embedding1']), dtype=np.float32)
        embedding2 = np.frombuffer(base64.b64decode(data['embedding2']), dtype=np.float32)
        
        # Compare embeddings
        is_match, similarity = face_service.compare_embeddings(embedding1, embedding2)
        
        response_data = {
            "success": True,
            "match": bool(is_match),
            "similarity": float(similarity),
            "threshold": 0.6
        }
        
        # Add debug info if available
        if not is_match and 'image1_base64' in data and 'image2_base64' in data:
            try:
                img1_data = base64.b64decode(data['image1_base64'])
                img2_data = base64.b64decode(data['image2_base64'])
                
                _, face_region1 = face_service.extract_face_embedding(img1_data)
                _, face_region2 = face_service.extract_face_embedding(img2_data)
                
                _, img1_buffer = face_service.cv2.imencode('.jpg', face_region1)
                _, img2_buffer = face_service.cv2.imencode('.jpg', face_region2)
                
                response_data["debug"] = {
                    "face1_image": base64.b64encode(img1_buffer).decode('utf-8'),
                    "face2_image": base64.b64encode(img2_buffer).decode('utf-8'),
                    "message": "Faces do not match. See extracted face regions."
                }
            except Exception as debug_error:
                logger.warning(f"Debug image processing failed: {str(debug_error)}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in compare_faces: {str(e)}")
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)