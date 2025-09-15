<<<<<<< HEAD
# Kiến trúc tổng quan

- `faceid-service`: sinh embedding và so khớp
- `user-service`: gọi faceid-service, lưu user+embedding
- `streamlit-app`: UI gọi user-service

Luồng chính:
1. Đăng ký: UI -> user-service `/register-face` -> gọi faceid-service `/encode-face` -> lưu DB
2. Đăng nhập: UI -> user-service `/login-face` -> gọi faceid-service `/encode-face` + `/compare-faces` -> trả kết quả
=======
# AI Attendance Manager - System Architecture

## Overview

The AI Attendance Manager is a microservices-based system that automates student attendance using facial recognition technology. The system consists of three main services working together to provide real-time attendance tracking with high accuracy and security.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Streamlit App  │    │  User Service   │    │ FaceID Service  │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│  (AI Engine)    │
│   Port: 8501    │    │   Port: 5002    │    │   Port: 5001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  User Interface │    │ Firebase        │    │ Face Detection  │
│  & Dashboard    │    │ Firestore       │    │ & Recognition   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Service Components

### 1. FaceID Service (Port 5001)
**Purpose:** Core AI engine for face detection and recognition

**Responsibilities:**
- Face detection from camera feed
- Face alignment and normalization
- Face encoding using CNN model
- Face comparison and matching
- Anti-spoofing (liveness detection)
- Mask detection
- Pose validation

**Key Features:**
- Uses InsightFace or similar ML models
- Configurable thresholds for detection accuracy
- Real-time processing (< 2 seconds)
- Support for multiple faces in single image

### 2. User Service (Port 5002)
**Purpose:** Business logic and data management

**Responsibilities:**
- Student registration and management
- Attendance recording and tracking
- Firebase integration (Firestore + Storage)
- API endpoints for frontend
- Authentication and authorization
- Data validation and processing

**Key Features:**
- RESTful API design
- Firebase Firestore for data storage
- Firebase Storage for image management
- JWT authentication
- Role-based access control

### 3. Streamlit App (Port 8501)
**Purpose:** Web-based user interface

**Responsibilities:**
- Student registration interface
- Attendance marking interface
- Admin dashboard
- Attendance reports and analytics
- Real-time camera integration
- User management interface

**Key Features:**
- Responsive web design
- Real-time camera preview
- Interactive dashboards
- Export functionality for reports
- Multi-user support

## Data Flow Architecture

### Student Registration Flow
```
1. Student uploads photo via Streamlit
2. Streamlit → User Service (/register)
3. User Service validates image
4. User Service → FaceID Service (/encode-face)
5. FaceID Service processes image and returns embedding
6. User Service saves student data + embedding to Firebase
7. Success confirmation returned to Streamlit
```

### Attendance Marking Flow
```
1. Student stands in front of camera
2. Camera captures image
3. Streamlit → User Service (/attendance)
4. User Service → FaceID Service (/encode-face)
5. FaceID Service returns face embedding
6. User Service retrieves all student embeddings from Firebase
7. User Service → FaceID Service (/compare-faces) for each student
8. Best match identified (if above threshold)
9. Attendance record created in Firebase
10. Success/failure returned to Streamlit
```

### Multi-Face Attendance Flow
```
1. Camera captures image with multiple faces
2. FaceID Service detects all faces in image
3. Each face is encoded separately
4. Each face is compared against student database
5. Multiple attendance records created
6. Results aggregated and returned
```

## Database Architecture

### Firebase Firestore Collections

**Users Collection:**
```javascript
{
  "username": "student@example.com",
  "name": "Student Name",
  "email": "student@example.com",
  "class_name": "Class A",
  "face_encoding": "base64_encoded_vector",
  "image_path": "faces/student@example.com/face.jpg",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Attendance Collection:**
```javascript
{
  "user_id": "student@example.com",
  "date": "2024-01-15",
  "timestamp": "2024-01-15T08:30:00Z",
  "status": "present", // or "absent"
  "image_path": "attendance/2024-01-15_image.jpg",
  "similarity_score": 0.85,
  "type": "attendance" // or "checkin", "checkout"
}
```

### Firebase Storage Structure
```
/uploads/
  /faces/
    /student@example.com/
      /face_student@example.com.jpg
  /attendance/
    /2024-01-15_student@example.com.jpg/
      /student@example.com/
        /attendance_2024-01-15_image.jpg
```

## Security Architecture

### Authentication & Authorization
- **JWT Tokens:** Secure API access
- **Role-based Access:** Admin, Teacher, Student roles
- **Firebase Auth:** Optional integration for advanced auth

### Data Protection
- **Encryption:** All facial data encrypted at rest
- **Privacy Compliance:** GDPR/CCPA compliant data handling
- **Secure Transmission:** HTTPS for all communications
- **Access Logging:** Complete audit trail

### Anti-Spoofing Measures
- **Liveness Detection:** Prevents photo/video spoofing
- **Pose Validation:** Ensures proper face positioning
- **Quality Checks:** Validates image quality and lighting
- **Multiple Validation:** Combines multiple detection methods

## Performance Architecture

### Scalability
- **Microservices:** Independent scaling of components
- **Load Balancing:** Support for multiple service instances
- **Database Optimization:** Efficient Firestore queries
- **Caching:** Face embedding caching for faster comparisons

### Performance Targets
- **Face Recognition:** < 2 seconds per face
- **Concurrent Users:** Support for 1000+ students
- **Uptime:** 99% availability during working hours
- **Accuracy:** 99%+ face recognition accuracy

## Technology Stack

### Backend Technologies
- **Python 3.10+:** Core programming language
- **Flask:** Web framework for services
- **InsightFace:** Face recognition library
- **OpenCV:** Image processing
- **NumPy:** Numerical computations
- **Firebase SDK:** Database and storage

### Frontend Technologies
- **Streamlit:** Web application framework
- **HTML5/CSS3:** User interface styling
- **JavaScript:** Interactive components
- **WebRTC:** Real-time camera access

### Machine Learning
- **TensorFlow/Keras:** Deep learning framework
- **CNN Models:** Convolutional neural networks
- **Face Embeddings:** 512-dimensional vectors
- **Similarity Metrics:** Cosine similarity for matching

## Deployment Architecture

### Development Environment
```bash
# Local development setup
faceid-service: python app.py (port 5001)
user-service: python run.py (port 5002)
streamlit-app: streamlit run app.py (port 8501)
```

### Production Considerations
- **Containerization:** Docker containers for each service
- **Orchestration:** Kubernetes for container management
- **Monitoring:** Application performance monitoring
- **Logging:** Centralized logging system
- **Backup:** Automated database backups

## Integration Points

### External Systems
- **Camera Systems:** IP cameras, USB webcams
- **Academic Systems:** LMS integration (future)
- **Notification Systems:** Email/SMS alerts (future)
- **Reporting Tools:** Export to Excel/PDF

### API Integration
- **RESTful APIs:** Standard HTTP endpoints
- **WebSocket:** Real-time communication (future)
- **GraphQL:** Advanced querying (future)
- **Webhook:** Event notifications (future)
>>>>>>> clean-branch
