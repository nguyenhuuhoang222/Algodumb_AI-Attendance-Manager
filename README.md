<<<<<<< HEAD
#Algodumb_AI-Attendance-Manager

Hệ thống nhận diện khuôn mặt gồm 3 phần:

- **faceid-service** (Flask): API encode/compare khuôn mặt (`/api/encode-face`, `/api/compare-faces`)
- **user-service** (Flask): Đăng ký/đăng nhập bằng khuôn mặt, lưu dữ liệu lên Firestore (hoặc file JSON demo)
- **streamlit-app** (Streamlit): Giao diện người dùng


## 1) Chạy `faceid-service` (port 5001)
=======
# AI Attendance Manager

## FPT ACADEMY INTERNATIONAL
## FPT - APTECH COMPUTER EDUCATION

### 1. Problem Definition

**Problem:**
Attendance management in educational institutions is a critical activity but is still mainly performed manually, leading to wasted time, errors, and proxy attendance.

**Objective:**
To develop an AI-powered Attendance System using facial recognition in order to:
- Automate student check-in/out
- Prevent fraudulent or proxy attendance  
- Increase accuracy and security of attendance records

### 2. Design Specifications

**Overview:**
The AI Attendance Manager leverages a camera at classroom entrances to capture student faces and compare them against a pre-trained database using a Machine Learning model (CNN). Upon a successful match, the student's presence is automatically marked.

The system provides:
- Student data management
- Real-time attendance tracking
- Daily and total attendance
- Attendance reports for teachers and administrators

**Scope:**
- Focuses exclusively on automated attendance using facial recognition
- Does not integrate with academic systems (LMS, SIS)
- Supports up to 1000 students in classroom/lecture halls

**Functional Requirements:**
1. **Data Collection** - Store students' facial data as digital profiles
2. **Face Detection** - Detect faces from real-time camera feed
3. **Face Alignment** - Normalize and enhance image quality
4. **Face Encoding** - Convert detected faces into stored records
5. **Machine Learning Model** - Use CNN (TensorFlow/Keras/PyTorch)
6. **Student Identification** - Identify students by ID or name
7. **Attendance Marking** - Record attendance/absence automatically
8. **Time Logging** - Log entry and exit times for students
9. **Data Storage** - Secure database (Firebase/NoSQL)
10. **User Interface** - Web-based and user-friendly
11. **Admin Dashboard** - Monitor attendance, student/search, management
12. **Fraud Prevention** - Prevent duplicate/proxy attendance
13. **Analytics & Reporting** - Generate attendance insights

**Non-Functional Requirements:**
1. **Performance** - Process recognition within <2 seconds
2. **Scalability** - Handle up to 1000 students without performance loss
3. **Usability** - Intuitive UI for teachers, admins, and students
4. **Availability** - Maintain at least 99% operation accuracy
5. **Reliability** - 99% uptime during working hours

**UI Design:**
- **Frontend:** HTML5, Streamlit (or equivalent)
- **Backend:** Flask/Django
- **Student View:** Automated attendance check-in, attendance history
- **Admin/Teacher View:** Dashboard, reports, student data management

### 3. System Architecture

**Microservices Architecture:**
- **faceid-service** (Flask): Face encode/compare API (`/api/encode-face`, `/api/compare-faces`)
- **user-service** (Flask): Student management, attendance recording, Firebase integration
- **streamlit-app** (Streamlit): Web-based user interface

**Data Flow:**
```
Student → Camera → Face Detection → Recognition → Attendance Marking → Database → Reporting
```

**System Architecture:**
```
Camera → Preprocessing → ML Model → Database → Web App (Teacher/Student)
```

### 4. Data Model

**Student Table:**
- student_id, name, class, image data, face_encoding

**Attendance Table:**
- record_id, student_id, checkin_time, checkout_time, status, date

**User Table:**
- id, username, password (hashed), role

### 5. Security Considerations

- Compliance with biometric data privacy regulations
- JWT authentication for secure API access
- Encryption of facial data storage
- Role-based access control (Admin, Teacher)

### 6. Installation Instructions

1. **Install Python 3.10**
2. **Install dependencies:** opencv, numpy, pandas, tensorflow/keras, facelib/dlib or (facial recognition lib from each folder: faceid-service, user-service and streamlit-app)
3. **Prepare dataset** (pre-process images)
4. **Run backend server** (faceid-service, user-service and streamlit-app)
5. **Launch frontend:** streamlit run app.py or equivalent web app
6. **Test system** using sample images/videos

### 7. Quick Start

## 1) Run `faceid-service` (port 5001)
>>>>>>> clean-branch
```bash
cd faceid-service
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

<<<<<<< HEAD
## 2) Chạy `user-service` (port 5002)
=======
## 2) Run `user-service` (port 5002)
>>>>>>> clean-branch
```bash
cd user-service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

<<<<<<< HEAD
# (Tuỳ chọn) cấu hình Firebase
# set GOOGLE_APPLICATION_CREDENTIALS, FIREBASE_PROJECT_ID

python run.py
```

## 3) Chạy `streamlit-app`
=======
# (Optional) configure Firebase
# set GOOGLE_APPLICATION_CREDENTIALS, FIREBASE_PROJECT_ID
#Filebase code already be applied in zip file for Techwiz 6 
python run.py
```

## 3) Run `streamlit-app`
>>>>>>> clean-branch
```bash
cd streamlit-app
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

<<<<<<< HEAD
## Kiến trúc & API
Xem thêm trong thư mục **docs/**.
    
=======
### 8. Test Data Used in Project

- Dataset built from real-time student images
- Images preprocessed (grayscale, resize)
- No pre-provided dataset used

### 9. Architecture & API
See more in the **docs/** folder.
>>>>>>> clean-branch
