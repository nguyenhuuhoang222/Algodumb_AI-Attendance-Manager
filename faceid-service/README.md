# FaceID Service

A RESTful API for face detection, face embedding (feature extraction), face comparison, and mask detection using InsightFace and OpenCV.

## Features

- **Face Detection:** Uses InsightFace (MTCNN/RetinaFace) for accurate face localization.
- **Face Embedding:** Extracts facial features using ArcFace model.
- **Face Comparison:** Compares two faces using cosine similarity.
- **Mask Detection:** Rejects faces with masks using custom heuristics.
- **RESTful API:** Easy-to-use endpoints for integration.
- **Fast Processing:** Optimized for quick response times.

## Requirements

- Python 3.8+
- See [requirements.txt](faceid-service/requirements.txt) for dependencies.

## Setup

```bash
cd faceid-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Service

```bash
python app.py
```

The service will run on `http://localhost:5001/` by default.

## API Endpoints

### 1. Health Check

- **GET** `/health`
- Returns service status.

### 2. Encode Face

- **POST** `/encode-face`
- **Form-data:** `image` (file)
- **Response:**  
  - `200 OK`: `{ "success": true, "embedding": <base64>, "face_image": <base64>, ... }`
  - `400 Bad Request`: Error details (e.g., mask detected, no face, multiple faces)

### 3. Compare Faces

- **POST** `/compare-faces`
- **JSON:**  
  - `embedding1`: base64 string  
  - `embedding2`: base64 string  
  - `threshold` (optional, default 0.6)
- **Response:**  
  - `200 OK`: `{ "success": true, "match": bool, "similarity": float, ... }`
  - `400 Bad Request`: Error details

## Example Usage

### Encode Face

```python
import requests

with open("test_images/person1.jpg", "rb") as f:
    r = requests.post("http://localhost:5001/encode-face", files={"image": f})
print(r.json())
```

### Compare Faces

```python
import requests

# Get embeddings for two images first (see above)
embedding1 = "..."  # base64 string
embedding2 = "..."

r = requests.post("http://localhost:5001/compare-faces", json={
    "embedding1": embedding1,
    "embedding2": embedding2
})
print(r.json())
```

## Testing

- See [test/](faceid-service/test/) for test scripts and sample images.
-   ```bash
source venv/bin/activate     # macOS/Linux
venv\Scripts\activate        # Windows
  ```
- Run tests:
  ```bash
  cd test
  pip install -r requirements_test.txt
  python test_accuracy.py
  python test_model.py
  python test_mask_detection.py
  python test_performance.py
  ```

## Notes

- The service rejects images with masks or without faces.
- Embeddings are returned as base64-encoded float32 arrays.
- For integration, see the main project [README.md](../README.md).

## Authors

- [Nguyen Huu Hoang]



