# AI Attendance Manager - Streamlit Frontend

A modern, responsive Streamlit application for managing student attendance using AI-powered face recognition.

## Features

### 🎯 Core Functionality
- **Real-time Face Recognition** - Advanced face detection and quality assessment
- **Automatic Attendance Marking** - Check-in/Check-out with face recognition
- **Student Registration** - Register new students with face data
- **Comprehensive Reports** - Detailed attendance analytics and exports
- **Dashboard Overview** - Real-time statistics and activity monitoring

### 🔧 Technical Features
- **Modular Architecture** - Clean separation of concerns
- **Service Integration** - Seamless integration with FaceID and User services
- **Error Handling** - Comprehensive error handling and user feedback
- **Session Management** - Advanced state management
- **Responsive Design** - Mobile-friendly interface
- **Real-time Processing** - Live video stream processing

## Architecture

```
streamlit-app/
├── app.py                 # Main application entry point
├── views/                 # UI View components
│   ├── dashboard_view.py
│   ├── students_list_view.py
│   ├── registration_view.py
│   ├── attendance_view.py
│   └── reports_view.py
├── components/            # Reusable UI components
│   └── video_processor.py
├── controllers/           # API integration layer
│   └── api_controller.py
├── utils/                 # Utility functions
│   ├── config.py
│   ├── session_manager.py
│   └── camera_utils.py
└── requirements.txt
```

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Services**
   - Start FaceID Service (port 5001)
   - Start User Service (port 5002)

3. **Run Application**
   ```bash
   streamlit run app.py
   ```

## Configuration

### Environment Variables
- `FACEID_SERVICE_URL` - FaceID service URL (default: http://localhost:5001)
- `USER_SERVICE_URL` - User service URL (default: http://localhost:5002)

### Service Integration
The application integrates with two backend services:

1. **FaceID Service** - Handles face recognition and encoding
2. **User Service** - Manages user data and attendance records

## Usage

### Dashboard
- View real-time attendance statistics
- Monitor system status
- Quick access to all features

### Student Management
- View all registered students
- Filter by class, status, or search term
- Export attendance data

### Registration
- Register new students with face data
- Real-time face quality assessment
- Automatic face capture when ready

### Attendance
- Mark check-in/check-out with face recognition
- Real-time face detection and quality feedback
- Automatic attendance recording

### Reports
- Generate detailed attendance reports
- Export data in CSV format
- View attendance trends and statistics

## API Integration

### FaceID Service Integration
- `POST /encode-face` - Encode face from image/video
- `POST /compare-faces` - Compare face embeddings
- `GET /health` - Service health check

### User Service Integration
- `GET /api/students` - Get students list
- `POST /api/register-student` - Register new student
- `POST /api/checkin` - Check-in student
- `POST /api/checkout` - Check-out student
- `GET /api/attendance-summary` - Get attendance summary

## Features

### Real-time Face Processing
- Advanced face detection using Haar cascades
- Quality assessment (sharpness, exposure, pose)
- Liveness detection to prevent spoofing
- Mask detection for security
- Automatic best frame selection

### User Experience
- Intuitive navigation with sidebar menu
- Real-time feedback and status updates
- Responsive design for all devices
- Comprehensive error handling
- Progress indicators and loading states

### Data Management
- Session state management
- Form validation and error handling
- Data export capabilities
- Real-time data synchronization

## Development

### Project Structure
- **Views** - UI components for each page
- **Components** - Reusable UI components
- **Controllers** - API integration layer
- **Utils** - Utility functions and helpers

### Adding New Features
1. Create new view in `views/` directory
2. Add API methods in `controllers/api_controller.py`
3. Update navigation in `app.py`
4. Add utility functions in `utils/` if needed

### Error Handling
- Comprehensive try-catch blocks
- User-friendly error messages
- Service status monitoring
- Graceful degradation

## Troubleshooting

### Common Issues
1. **Camera not working** - Check browser permissions
2. **Face not detected** - Ensure good lighting and clear visibility
3. **Service errors** - Check if backend services are running
4. **Quality issues** - Adjust lighting and position

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export STREAMLIT_LOGGER_LEVEL=debug
```

## License

This project is part of the AI Attendance Manager system.
