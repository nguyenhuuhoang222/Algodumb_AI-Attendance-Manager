# User Service - AI Attendance Manager

A Flask-based microservice that handles student management, attendance recording, and Firebase integration for the AI Attendance Manager system.

## Features

### 🎯 Core Functionality
- **Student Registration** - Register new students with facial data
- **Attendance Management** - Mark attendance using face recognition
- **Multi-face Support** - Handle multiple students in single image
- **Bulk Operations** - Mark absent students in bulk
- **Data Analytics** - Generate attendance statistics and reports

### 🔧 Technical Features
- **Firebase Integration** - Firestore database and Storage
- **Face Recognition API** - Integration with FaceID service
- **RESTful API** - Clean API endpoints
- **Error Handling** - Comprehensive error management
- **Logging** - Structured logging for monitoring
- **Data Validation** - Input validation and sanitization

## Architecture

```
user-service/
├── app/
│   ├── __init__.py
│   ├── config/
│   │   └── settings.py          # Application configuration
│   ├── controllers/
│   │   ├── auth_controller.py   # Authentication endpoints
│   │   └── attendance_controller.py  # Attendance endpoints
│   ├── models/
│   │   └── user_models.py       # Data models
│   ├── repositories/
│   │   ├── user_repository.py   # User data access
│   │   └── attendance_repository.py  # Attendance data access
│   ├── services/
│   │   ├── user_service.py      # User business logic
│   │   ├── attendance_service.py # Attendance business logic
│   │   ├── face_auth_service.py  # Face authentication
│   │   ├── face_recognition_service.py # Face recognition integration
│   │   ├── firebase_service.py  # Firebase integration
│   │   └── storage_service.py   # File storage management
│   └── utils/
│       ├── image_processor.py   # Image processing utilities
│       ├── logger.py           # Logging configuration
│       └── validators.py       # Input validation
├── run.py                      # Application entry point
├── requirements.txt            # Python dependencies
└── test_images/               # Test images for development
```

## Installation

1. **Create Virtual Environment**
   ```bash
   cd user-service
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Firebase (Optional)**
   ```bash
   # Set environment variables
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
   export FIREBASE_PROJECT_ID="your-project-id"
   ```

## Running the Service

```bash
python run.py
```

The service will run on `http://localhost:5002` by default.

## API Endpoints

### Authentication & User Management

#### POST /register
Register a new student with facial data.

**Request:**
```http
POST /register
Content-Type: multipart/form-data

Form Data:
- name: string (required) - Student's full name
- email: string (required) - Student's email or ID
- image: file (required) - Face image file
```

**Response:**
```json
{
  "success": true,
  "message": "Registration successful",
  "user_id": "student@example.com"
}
```

#### GET /users
Get list of all registered students.

#### GET /users/search
Search students by name.

#### GET /users/{user_id}
Get specific student information.

#### PUT /users/{user_id}/image
Update student's face image.

### Attendance Management

#### POST /attendance
Mark attendance for a single student.

**Request:**
```http
POST /attendance
Content-Type: multipart/form-data

Form Data:
- image: file (required) - Face image for attendance
- classId: string (optional) - Class ID for filtering
```

#### POST /attendance/multi
Mark attendance for multiple students in single image.

#### GET /attendance/list
Get attendance list for specific date.

#### GET /attendance/history
Get attendance history for specific student.

#### POST /attendance/mark-absent
Mark multiple students as absent.

#### GET /attendance/statistics
Get attendance statistics for date range.

## Configuration

### Environment Variables
- `FIREBASE_PROJECT_ID` - Firebase project ID
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to Firebase credentials
- `FACEID_SERVICE_URL` - FaceID service URL (default: http://localhost:5001)
- `MAX_IMAGE_SIZE` - Maximum image file size (default: 2MB)
- `FACEID_TIMEOUT` - FaceID service timeout (default: 1500ms)

### Firebase Configuration
The service supports both Firebase and local file storage:

**Firebase Mode (Production):**
- Requires Firebase credentials
- Uses Firestore for data storage
- Uses Firebase Storage for images

**Local Mode (Development):**
- Stores data in local JSON files
- Stores images in local directories
- No Firebase setup required

## Service Integration

### FaceID Service Integration
The service integrates with FaceID service for face recognition:

```python
# Face encoding
encode_result = face_service.encode_face(image_bytes)

# Face comparison
compare_result = face_service.compare_faces(embedding1, embedding2)
```

### Firebase Integration
```python
# Save user data
firebase_service.save_user(user_data)

# Get attendance records
attendance_list = firebase_service.get_attendance_by_date(date)
```

## Data Models

### User Model
```python
class User:
    username: str
    name: str
    email: str
    face_encoding: str  # Base64 encoded
    image_path: str
    created_at: datetime
    updated_at: datetime
```

### AttendanceRecord Model
```python
class AttendanceRecord:
    user_id: str
    date: str
    timestamp: datetime
    status: str  # "present" or "absent"
    image_path: str
    similarity_score: float
    type: str  # "attendance", "checkin", "checkout"
```

## Error Handling

### Common Error Responses
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE"
}
```

### Error Codes
- `INVALID_IMAGE` - Invalid image format
- `STUDENT_NOT_FOUND` - Student ID not found
- `NO_MATCH_FOUND` - No matching student found
- `FACE_MISMATCH` - Face does not match student
- `SERVER_ERROR` - Internal server error

## Logging

The service uses structured logging:

```python
# Example log entry
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "user-service",
  "action": "face_recognition",
  "user_id": "student@example.com",
  "duration_ms": 1500,
  "success": true
}
```

## Testing

### Test Images
Use images in `test_images/` directory for development testing.

### API Testing
```bash
# Test registration
curl -X POST http://localhost:5002/register \
  -F "name=Test Student" \
  -F "email=test@example.com" \
  -F "image=@test_images/person1.jpg"

# Test attendance
curl -X POST http://localhost:5002/attendance \
  -F "image=@test_images/person1.jpg"
```

## Performance

### Response Time Targets
- **Student Registration:** < 3 seconds
- **Face Recognition:** < 2 seconds
- **Attendance Marking:** < 2 seconds
- **Data Retrieval:** < 1 second

### Scalability
- **Concurrent Users:** 100+ simultaneous users
- **Database Records:** 10,000+ students
- **Image Storage:** 100GB+ storage capacity

## Security

### Data Protection
- **Image Encryption:** All images encrypted at rest
- **API Authentication:** JWT token validation
- **Input Validation:** Comprehensive input sanitization
- **Access Control:** Role-based permissions

### Privacy Compliance
- **Data Retention:** Configurable data retention policies
- **GDPR Compliance:** Right to deletion and data portability
- **Audit Logging:** Complete audit trail

## Troubleshooting

### Common Issues

1. **FaceID Service Connection Error**
   - Check if FaceID service is running on port 5001
   - Verify network connectivity

2. **Firebase Authentication Error**
   - Check Firebase credentials file path
   - Verify Firebase project configuration

3. **Image Processing Error**
   - Check image format and size
   - Verify file permissions

### Debug Mode
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python run.py
```

## Development

### Adding New Features
1. Create service in `services/` directory
2. Add repository methods in `repositories/`
3. Create controller endpoints in `controllers/`
4. Update models if needed
5. Add tests and documentation

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Add docstrings for all functions
- Include error handling

## License

This project is part of the AI Attendance Manager system.
