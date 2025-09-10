    Face Detection: Uses MTCNN for accurate face detection

    Face Encoding: Extracts facial features using ArcFace model

    Face Comparison: Compares two faces using cosine similarity

    RESTful API: Easy-to-use endpoints for integration

    Fast Processing: Optimized for quick response times


RESTful API { 
    /health(GET): Check if the service is running
    /encode-face(POST):Extract facial features from an image
    /compare-faces(POST):Compare two facial embeddings
    /compare-images(POST): Compare faces from two images 
}
   