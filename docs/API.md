# AI Attendance Manager - API Documentation

## Overview

The AI Attendance Manager provides RESTful APIs across three microservices for comprehensive attendance management using facial recognition technology.

## Service Endpoints

### FaceID Service (Port 5001)

**Base URL:** `http://localhost:5001`

#### POST /api/encode-face
**Purpose:** Encode a face image into a face embedding vector

**Request:**
```http
POST /api/encode-face
Content-Type: multipart/form-data

Form Data:
- image: file (required) - Face image file (JPEG, PNG, JPG)
```

**Response:**
```json
{
  "success": true,
  "embedding": [0.123, -0.456, 0.789, ...], // 512-dimensional float array
  "face_detected": true,
  "quality_score": 0.95,
  "processing_time": 1.2
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "No face detected in image",
  "code": "NO_FACE_DETECTED"
}
```

#### POST /api/compare-faces
**Purpose:** Compare two face embeddings and determine if they match

**Request:**
```http
POST /api/compare-faces
Content-Type: application/json

{
  "embedding1": [0.123, -0.456, 0.789, ...],
  "embedding2": [0.124, -0.455, 0.790, ...],
  "threshold": 0.7 // optional, default: 0.7
}
```

**Response:**
```json
{
  "success": true,
  "match": true,
  "similarity": 0.85,
  "distance": 0.15,
  "threshold_used": 0.7
}
```

### User Service (Port 5002)

**Base URL:** `http://localhost:5002`

#### POST /register
**Purpose:** Register a new student with facial data

**Request:**
```http
POST /register
Content-Type: multipart/form-data

Form Data:
- name: string (required) - Student's full name
- email: string (required) - Student's email or student ID
- image: file (required) - Face image file
```

**Response:**
```json
{
  "success": true,
  "message": "Registration successful",
  "user_id": "student@example.com",
  "face_encoding_created": true
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid image format",
  "code": "INVALID_IMAGE"
}
```

#### POST /attendance
**Purpose:** Mark attendance for a single student

**Request:**
```http
POST /attendance
Content-Type: multipart/form-data

Form Data:
- image: file (required) - Face image for attendance
- classId: string (optional) - Class ID for filtering
```

**Response:**
```json
{
  "success": true,
  "message": "Attendance marked successfully",
  "matched_user": {
    "user_id": "student@example.com",
    "name": "Student Name",
    "similarity_score": 0.85
  },
  "attendance_record": {
    "record_id": "att_123456",
    "timestamp": "2024-01-15T08:30:00Z",
    "status": "present"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "No matching student found",
  "code": "NO_MATCH_FOUND"
}
```

#### POST /attendance/multi
**Purpose:** Mark attendance for multiple students in a single image

**Request:**
```http
POST /attendance/multi
Content-Type: multipart/form-data

Form Data:
- image: file (required) - Image containing multiple faces
- note: string (optional) - Additional notes
- classId: string (optional) - Class ID for filtering
```

**Response:**
```json
{
  "success": true,
  "message": "Multi-face attendance processed",
  "results": [
    {
      "user_id": "student1@example.com",
      "name": "Student One",
      "similarity_score": 0.89,
      "attendance_record": {
        "record_id": "att_123456",
        "timestamp": "2024-01-15T08:30:00Z",
        "status": "present"
      }
    },
    {
      "user_id": "student2@example.com",
      "name": "Student Two", 
      "similarity_score": 0.82,
      "attendance_record": {
        "record_id": "att_123457",
        "timestamp": "2024-01-15T08:30:00Z",
        "status": "present"
      }
    }
  ],
  "total_faces_detected": 2,
  "total_matches": 2
}
```

#### GET /attendance/list
**Purpose:** Get attendance list for a specific date

**Request:**
```http
GET /attendance/list?date=2024-01-15&classId=class_a
```

**Response:**
```json
{
  "success": true,
  "date": "2024-01-15",
  "attendance_list": [
    {
      "user_id": "student1@example.com",
      "name": "Student One",
      "status": "present",
      "timestamp": "2024-01-15T08:30:00Z",
      "similarity_score": 0.89
    },
    {
      "user_id": "student2@example.com",
      "name": "Student Two",
      "status": "absent",
      "timestamp": null,
      "similarity_score": null
    }
  ],
  "total_present": 1,
  "total_absent": 1,
  "total_students": 2
}
```

#### GET /attendance/history
**Purpose:** Get attendance history for a specific student

**Request:**
```http
GET /attendance/history?userId=student@example.com&startDate=2024-01-01&endDate=2024-01-31
```

**Response:**
```json
{
  "success": true,
  "student": {
    "user_id": "student@example.com",
    "name": "Student Name"
  },
  "attendance_history": [
    {
      "date": "2024-01-15",
      "status": "present",
      "timestamp": "2024-01-15T08:30:00Z"
    },
    {
      "date": "2024-01-14",
      "status": "absent",
      "timestamp": null
    }
  ],
  "total_days": 2,
  "present_days": 1,
  "absent_days": 1,
  "attendance_rate": 50.0
}
```

#### POST /attendance/mark-absent
**Purpose:** Mark multiple students as absent for a specific date

**Request:**
```http
POST /attendance/mark-absent
Content-Type: application/json

{
  "user_ids": ["student1@example.com", "student2@example.com"],
  "date": "2024-01-15"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Marked 2 students absent",
  "marked_count": 2,
  "marked_students": [
    {
      "user_id": "student1@example.com",
      "name": "Student One"
    },
    {
      "user_id": "student2@example.com",
      "name": "Student Two"
    }
  ]
}
```

#### GET /attendance/statistics
**Purpose:** Get attendance statistics for a date range

**Request:**
```http
GET /attendance/statistics?startDate=2024-01-01&endDate=2024-01-31&classId=class_a
```

**Response:**
```json
{
  "success": true,
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "statistics": {
    "total_students": 50,
    "total_days": 31,
    "average_attendance_rate": 85.5,
    "daily_attendance": [
      {
        "date": "2024-01-15",
        "present_count": 45,
        "absent_count": 5,
        "attendance_rate": 90.0
      }
    ],
    "student_attendance": [
      {
        "user_id": "student1@example.com",
        "name": "Student One",
        "present_days": 28,
        "absent_days": 3,
        "attendance_rate": 90.3
      }
    ]
  }
}
```

#### GET /users
**Purpose:** Get list of all registered students

**Request:**
```http
GET /users
```

**Response:**
```json
{
  "success": true,
  "users": [
    {
      "user_id": "student1@example.com",
      "name": "Student One",
      "email": "student1@example.com",
      "class_name": "Class A",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 1
}
```

#### GET /users/search
**Purpose:** Search students by name

**Request:**
```http
GET /users/search?name=John
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "user_id": "john.doe@example.com",
      "name": "John Doe",
      "email": "john.doe@example.com",
      "class_name": "Class A"
    }
  ],
  "total_found": 1
}
```

#### GET /users/{user_id}
**Purpose:** Get specific student information

**Request:**
```http
GET /users/student@example.com
```

**Response:**
```json
{
  "success": true,
  "user": {
    "user_id": "student@example.com",
    "name": "Student Name",
    "email": "student@example.com",
    "class_name": "Class A",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

#### PUT /users/{user_id}/image
**Purpose:** Update student's face image

**Request:**
```http
PUT /users/student@example.com/image
Content-Type: multipart/form-data

Form Data:
- image: file (required) - New face image
```

**Response:**
```json
{
  "success": true,
  "message": "Image update successful",
  "user_id": "student@example.com",
  "face_encoding_updated": true
}
```

## Error Codes

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_IMAGE` | Invalid image format or corrupted file |
| `NO_FACE_DETECTED` | No face detected in the uploaded image |
| `MULTIPLE_FACES` | Multiple faces detected when single face expected |
| `IMAGE_TOO_LARGE` | Image file size exceeds limit |
| `STUDENT_NOT_FOUND` | Student ID not found in database |
| `NO_MATCH_FOUND` | No matching student found for attendance |
| `FACE_MISMATCH` | Face does not match registered student |
| `ATTENDANCE_EXISTS` | Attendance already marked for this date |
| `INVALID_DATE` | Invalid date format provided |
| `MISSING_PARAMETERS` | Required parameters missing |
| `SERVER_ERROR` | Internal server error |

### HTTP Status Codes

| Status | Description |
|--------|-------------|
| `200` | Success |
| `400` | Bad Request - Invalid input |
| `401` | Unauthorized - Authentication required |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Resource not found |
| `413` | Payload Too Large - Image file too large |
| `500` | Internal Server Error |
| `503` | Service Unavailable - FaceID service down |

## Authentication

### JWT Token Authentication
```http
Authorization: Bearer <jwt_token>
```

### API Key Authentication (Future)
```http
X-API-Key: <api_key>
```

## Rate Limiting

- **FaceID Service:** 100 requests per minute per IP
- **User Service:** 200 requests per minute per IP
- **Burst Limit:** 10 requests per second

## Response Format

All API responses follow this standard format:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## WebSocket Events (Future)

### Real-time Attendance Updates
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:5002/ws');

// Listen for attendance events
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  if (data.type === 'attendance_update') {
    console.log('New attendance:', data.attendance);
  }
};
```

## SDK Examples

### Python SDK Example
```python
import requests

# Register student
files = {'image': open('student_photo.jpg', 'rb')}
data = {'name': 'John Doe', 'email': 'john@example.com'}
response = requests.post('http://localhost:5002/register', files=files, data=data)
print(response.json())

# Mark attendance
files = {'image': open('attendance_photo.jpg', 'rb')}
response = requests.post('http://localhost:5002/attendance', files=files)
print(response.json())
```

### JavaScript SDK Example
```javascript
// Register student
const formData = new FormData();
formData.append('name', 'John Doe');
formData.append('email', 'john@example.com');
formData.append('image', fileInput.files[0]);

fetch('http://localhost:5002/register', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));

// Mark attendance
const formData = new FormData();
formData.append('image', fileInput.files[0]);

fetch('http://localhost:5002/attendance', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```