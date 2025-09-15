import streamlit as st
import cv2
import numpy as np
import time
import logging
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from controllers.api_controller import api_controller
from components import ReadinessProcessor
from components.simple_camera import render_simple_camera
from utils.session_manager import SessionManager
from utils.camera_utils import inject_camera_guides, reset_registration_states

def auto_refresh_ui():
    if st.session_state.get('start_camera', False):
        time.sleep(0.5)
        st.rerun()

logger = logging.getLogger(__name__)

def render_registration():
    st.markdown("""
    <div class="registration-header">
        <div class="header-content">
            <h1 class="main-title">Automatic Student Registration</h1>
            <p class="subtitle">Fully automated registration system - Just fill in the information and take a photo</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display success notification if exists
    if st.session_state.get('registration_success'):
        success_data = st.session_state.registration_success
        current_time = time.time()
        
        # Show notification for 5 seconds
        if current_time - success_data.get('timestamp', 0) < 5:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #28a745, #20c997); 
                        color: white; padding: 20px; border-radius: 12px; 
                        margin: 15px 0; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
                        border-left: 5px solid #155724; animation: slideIn 0.5s ease-out;">
                <h4 style="margin: 0 0 15px 0; color: white; font-size: 1.3em;">
                    Registration Successful
                </h4>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                    <p style="margin: 5px 0;"><strong>Student ID:</strong> {success_data.get('student_id', 'N/A')}</p>
                    <p style="margin: 5px 0;"><strong>Full Name:</strong> {success_data.get('full_name', 'N/A')}</p>
                    <p style="margin: 5px 0;"><strong>Class Name:</strong> {success_data.get('class_name', 'N/A')}</p>
                    <p style="margin: 5px 0;"><strong>Username:</strong> {success_data.get('username', 'N/A')}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Clear success notification after 5 seconds
            st.session_state.registration_success = None
    
    # Display error notification if exists
    if st.session_state.get('registration_error'):
        error_data = st.session_state.registration_error
        current_time = time.time()
        
        # Show notification for 5 seconds
        if current_time - error_data.get('timestamp', 0) < 5:
            error_display = error_data.get('error_msg', 'Registration failed')
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #dc3545, #c82333); 
                        color: white; padding: 20px; border-radius: 12px; 
                        margin: 15px 0; box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
                        border-left: 5px solid #721c24; animation: slideIn 0.5s ease-out;">
                <h4 style="margin: 0 0 15px 0; color: white; font-size: 1.3em;">
                    Registration Failed
                </h4>
                <p style="margin: 0; color: white; font-size: 1.1em;">{error_display}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Clear error notification after 5 seconds
            st.session_state.registration_error = None
    
    session_manager = SessionManager()
    
    st.markdown("### Step 1: Student Information")
    with st.form("student_registration_form", clear_on_submit=False):
        render_student_form()
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            submitted = st.form_submit_button("Start Camera Capture", use_container_width=True, type="primary")
        
        with col2:
            reset_form = st.form_submit_button("Reset Form", use_container_width=True, type="secondary")
        
        if submitted:
            form_data = st.session_state.get('registration_data', {})
            required_fields = ['full_name', 'username']
            missing_fields = [field for field in required_fields if not form_data.get(field)]
            
            if missing_fields:
                field_names = {'full_name': 'Full Name', 'username': 'Username'}
                missing_names = [field_names[field] for field in missing_fields]
                st.error(f"Please fill in all required fields: {', '.join(missing_names)}")
            else:
                st.session_state.start_camera = True
            st.rerun()
        
        if reset_form:
            reset_registration_states()
            st.rerun()
    
    st.markdown("### Step 2: Automatic Photo Capture")
    
    if st.session_state.get('start_camera', False):
        render_auto_camera_section()
    else:
        st.markdown("""
        <div style="background: #f8f9fa; border: 2px dashed #dee2e6; padding: 30px; margin: 20px 0; border-radius: 12px; text-align: center;">
            <h3 style="color: #495057; margin-bottom: 15px;">Camera Not Started</h3>
            <p style="color: #6c757d; margin-bottom: 20px;">Please fill in student information and click "Start Camera Capture" to activate the camera</p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.get('reg_best_bytes') and not st.session_state.get('reg_ready', False):
        st.markdown("### Step 3: Registration Processing")
        st.info("Processing image and registering student...")
        
        import io
        from PIL import Image
        img_bytes = st.session_state.reg_best_bytes
        img = Image.open(io.BytesIO(img_bytes))
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(img, caption="Captured Face Image", use_container_width=True)
        
        handle_registration_submission()
    
    if st.session_state.get('start_camera', False):
        st.markdown("---")
        st.markdown("### Camera Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Restart Camera", use_container_width=True, key="restart_camera_control"):
                st.session_state.form_reset_counter = st.session_state.get('form_reset_counter', 0) + 1
                st.session_state.start_camera = True
                st.rerun()
        
        with col2:
            if st.button("Stop Camera", use_container_width=True, key="stop_camera_control"):
                st.session_state.start_camera = False
                st.rerun()
        
        col3, col4 = st.columns(2)
        
        with col3:
            if st.button("Reset Timer", use_container_width=True, key="reset_timer_control"):
                st.session_state.timer_reset_requested = True
                st.rerun()
        
        with col4:
            if st.button("Start Timer", use_container_width=True, key="start_timer_control"):
                st.session_state.timer_start_requested = True
                st.rerun()
    

def process_video_stream(ctx_reg):
    if not ctx_reg or not ctx_reg.state.playing:
        return
    
    processor = ctx_reg.video_processor
    if not processor:
        return
    
    readiness = getattr(processor, 'readiness', 0.0)
    ok_frames = getattr(processor, 'ok_frames', 0)
    face_ok = getattr(processor, 'face_ok', False)
    liveness_ok = getattr(processor, 'liveness_ok', False)
    mask_suspect = getattr(processor, 'mask_suspect', False)
    best_frame = getattr(processor, 'best_frame', None)
    
    if processor.is_ready_for_capture():
        if not st.session_state.get('reg_ready', False):
            st.session_state.reg_ready = True
            st.success("Face detected and ready for capture!")
        
        if best_frame is not None and not st.session_state.get('reg_best_bytes'):
            _, buffer = cv2.imencode('.jpg', best_frame)
            frame_bytes = buffer.tobytes()
            st.session_state.reg_best_bytes = frame_bytes
            
            st.image(best_frame, caption="Captured Face", use_container_width=True)
            st.success("Face captured successfully!")
            
            try:
                if ctx_reg and hasattr(ctx_reg, 'stop'):
                    ctx_reg.stop()
            except Exception:
                pass
            
            form_data = st.session_state.get('registration_data', {})
            required_fields = ['full_name', 'username']
            has_required_data = all(form_data.get(field) for field in required_fields)
            
            if has_required_data:
                import time
                timestamp = int(time.time())
                form_data['student_id'] = f"SV{timestamp % 100000:05d}"
                st.session_state.registration_data = form_data
            
            if has_required_data:
                st.info("Automatically registering student...")
                handle_registration_submission()
            else:
                st.warning("Please fill in all student information before taking a photo")
            
            st.rerun()
    else:
        pass

def render_auto_camera_section():
    st.markdown("""
    <div class="auto-camera-instructions">
        <div class="instruction-header">
            <h4> Photo Capture Guide</h4>
        </div>
        <div class="instruction-list">
            <div class="instruction-item">
                <span>1. Place your face in the frame</span>
            </div>
            <div class="instruction-item">
                <span>2. Wait for the green light and hold still</span>
            </div>
            <div class="instruction-item">
                <span>3. System automatically captures and registers</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    inject_camera_guides()
    
    if st.session_state.get('timer_reset_requested', False):
        st.session_state.timer_reset_requested = False
        st.info("Timer has been reset for the next person")
    
    if st.session_state.get('timer_start_requested', False):
        st.session_state.timer_start_requested = False
        st.info("Timer has been started manually")
    
    if st.session_state.get('capture_start_requested', False):
        st.session_state.capture_start_requested = False
        st.info("Capture has been started manually")
    
    webrtc_key = f"webrtc_auto_register_{st.session_state.get('form_reset_counter', 0)}"
    
    if st.session_state.get('start_camera', False):
        st.info("Starting camera... If the camera does not load, please click the 'Restart Camera' button below.")
    
    ctx_reg = webrtc_streamer(
        key=webrtc_key,
        mode=WebRtcMode.SENDRECV,
        media_stream_constraints={
            "video": {
                "facingMode": "user",
                "width": {"ideal": 640, "min": 320},
                "height": {"ideal": 480, "min": 240}
            },
            "audio": False
        },
        rtc_configuration={
            "iceServers": [
                {"urls": ["stun:stun.l.google.com:19302"]},
                {"urls": ["stun:stun1.l.google.com:19302"]}
            ]
        },
        video_processor_factory=ReadinessProcessor,
        video_html_attrs={
            "autoPlay": True,
            "playsInline": True,
            "muted": True,
            "controls": False,
            "style": {
                "width": "100%",
                "maxWidth": "500px",
                "height": "auto",
                "borderRadius": "10px",
                "boxShadow": "0 4px 15px rgba(0,0,0,0.1)"
            }
        },
        async_processing=True
    )
    
    if ctx_reg and ctx_reg.state.playing:
        if st.session_state.get('timer_reset_requested', False):
            if hasattr(ctx_reg, 'video_processor') and ctx_reg.video_processor:
                ctx_reg.video_processor.reset_person_timer()
            st.session_state.timer_reset_requested = False
        
        if st.session_state.get('timer_start_requested', False):
            if hasattr(ctx_reg, 'video_processor') and ctx_reg.video_processor:
                ctx_reg.video_processor.start_person_timer()
            st.session_state.timer_start_requested = False
        
        if st.session_state.get('capture_start_requested', False):
            if hasattr(ctx_reg, 'video_processor') and ctx_reg.video_processor:
                ctx_reg.video_processor.start_best_frame_capture()
            st.session_state.capture_start_requested = False
        
        process_auto_capture(ctx_reg)
    elif ctx_reg and ctx_reg.state.playing is False:
        if st.session_state.get('reg_best_bytes'):
            st.info("Camera stopped after capture. Processing registration...")
        else:
            processor = getattr(ctx_reg, 'video_processor', None)
            if processor and hasattr(processor, 'timer_expired') and processor.timer_expired:
                if hasattr(processor, 'status_text') and "Liveness check failed" in processor.status_text:
                    st.error("Liveness Check Failed!")
                    st.error("The system did not detect your movement within 5 seconds.")
                    st.error("Instructions: Please move your head slightly or blink to verify liveness.")
                    st.error("Click 'Restart Camera' to try again.")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if st.button("Restart Camera", width='stretch', key="restart_camera_4"):
                            st.session_state.form_reset_counter = st.session_state.get('form_reset_counter', 0) + 1
                            st.session_state.start_camera = True
                            st.rerun()
                    
                    with col2:
                        if st.button("Stop Camera", width='stretch', key="stop_camera_4"):
                            st.session_state.start_camera = False
                            st.rerun()
                    
                    with col3:
                        if st.button("Reset Timer", width='stretch', key="reset_timer_4"):
                            st.session_state.timer_reset_requested = True
                            st.rerun()
                    
                    with col4:
                        if st.button("Start Timer", width='stretch', key="start_timer_4"):
                            st.session_state.timer_start_requested = True
                            st.rerun()
                else:
                    st.warning("Time's up!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if st.button("Restart Camera", width='stretch', key="restart_camera_5"):
                            st.session_state.form_reset_counter = st.session_state.get('form_reset_counter', 0) + 1
                            st.session_state.start_camera = True
                            st.rerun()
                    
                    with col2:
                        if st.button("Stop Camera", width='stretch', key="stop_camera_5"):
                            st.session_state.start_camera = False
                            st.rerun()
                    
                    with col3:
                        if st.button("Reset Timer", width='stretch', key="reset_timer_5"):
                            st.session_state.timer_reset_requested = True
                            st.rerun()
                    
                    with col4:
                        if st.button("Start Timer", width='stretch', key="start_timer_5"):
                            st.session_state.timer_start_requested = True
                            st.rerun()
            else:
                st.warning("Camera has stopped. Click the button below to restart.")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("Restart Camera", width='stretch', key="restart_camera_3"):
                    st.session_state.form_reset_counter = st.session_state.get('form_reset_counter', 0) + 1
                    st.session_state.start_camera = True
                    st.rerun()
            
            with col2:
                if st.button("Stop Camera", width='stretch', key="stop_camera_3"):
                    st.session_state.start_camera = False
                    st.rerun()
            
            with col3:
                if st.button("Reset Timer", width='stretch', key="reset_timer_3"):
                    st.session_state.timer_reset_requested = True
                    st.rerun()
            
            with col4:
                if st.button("Start Timer", width='stretch', key="start_timer_3"):
                    st.session_state.timer_start_requested = True
                    st.rerun()
    else:
        st.warning("Starting camera...")

def render_simple_camera_section():
    st.markdown("### Simple Photo Capture")
    
    render_simple_camera()
    
    if 'photo_bytes' in st.session_state:
        st.success("Photo captured! You can now submit the registration form.")

def render_student_form():
    st.markdown("""
    <div class="form-container">
        <div class="form-header">
            <h4>Detailed Information</h4>
            <p>Please fill in all student information before taking a photo. The student ID will be automatically generated. The system will automatically register when a face is detected.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        import time
        timestamp = int(time.time())
        auto_id = f"SV{timestamp % 100000:05d}"
        st.session_state.student_id_input = auto_id
        student_id = auto_id
        
        st.markdown(f"""
        <div class="auto-generated-field">
            <label class="field-label">Student ID</label>
            <div class="field-value">
                <span class="student-id">{student_id}</span>
                <span class="auto-badge">Auto-generated</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        full_name = st.text_input(
            "Full Name *",
            placeholder="Enter full name",
            help="Full name of the student (required)",
            key=f"full_name_input_{st.session_state.get('form_reset_counter', 0)}"
        )
        
        class_name = st.text_input(
            "Class Name",
            placeholder="Enter class name",
            help="Class or course name (optional)",
            key=f"class_name_input_{st.session_state.get('form_reset_counter', 0)}"
        )
    
    with col2:
        username = st.text_input(
            "Username *",
            placeholder="Enter username",
            help="Username for the student (required)",
            key=f"username_input_{st.session_state.get('form_reset_counter', 0)}"
        )
        
        email = st.text_input(
            "E-mail",
            placeholder="Enter email address",
            help="Email address (optional)",
            key=f"email_input_{st.session_state.get('form_reset_counter', 0)}"
        )
        
        if not student_id:
            import time
            timestamp = int(time.time())
            student_id = f"SV{timestamp % 100000:05d}"
            st.session_state.student_id_input = student_id
        
        form_data = {}
        if student_id:
            form_data['student_id'] = student_id
        if full_name:
            form_data['full_name'] = full_name
        if class_name:
            form_data['class_name'] = class_name
        if username:
            form_data['username'] = username
        if email:
            form_data['email'] = email
            
        st.session_state.registration_data = form_data

def render_face_capture_section():
    st.markdown("""
    <div class="capture-instructions">
        <div class="instruction-header">
            <h4>Photo Capture Instructions</h4>
        </div>
        <div class="instruction-list">
            <div class="instruction-item">
                <span>Place your face within the camera frame</span>
            </div>
            <div class="instruction-item">
                <span>Ensure good and clear lighting</span>
            </div>
            <div class="instruction-item">
                <span>Look straight into the camera</span>
            </div>
            <div class="instruction-item">
                <span>Remove masks and sunglasses</span>
            </div>
            <div class="instruction-item">
                <span>Wait for the green border to appear</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    inject_camera_guides()
    
    ctx_reg = webrtc_streamer(
        key="webrtc_register",
        mode=WebRtcMode.SENDRECV,
        media_stream_constraints={
            "video": {
                "facingMode": "user",
                "width": {"ideal": 640, "min": 320},
                "height": {"ideal": 480, "min": 240}
            },
            "audio": False
        },
        rtc_configuration={
            "iceServers": [
                {"urls": ["stun:stun.l.google.com:19302"]},
                {"urls": ["stun:stun1.l.google.com:19302"]}
            ]
        },
        video_processor_factory=ReadinessProcessor,
        video_html_attrs={
            "autoPlay": True,
            "playsInline": True,
            "muted": True,
            "controls": False,
            "style": {
                "width": "100%",
                "maxWidth": "500px",
                "height": "auto",
                "borderRadius": "10px",
                "boxShadow": "0 4px 15px rgba(0,0,0,0.1)"
            }
        },
        async_processing=True
    )
    
    if ctx_reg and ctx_reg.state.playing:
        process_video_stream(ctx_reg)
        
        process_auto_capture(ctx_reg)
        
        if ctx_reg.video_processor:
            processor = ctx_reg.video_processor
            is_ready = processor.is_ready_for_capture()
            
            if is_ready:
                st.markdown("""
                <div class="status-ready">
                    <div class="status-icon"></div>
                    <div class="status-text">
                        <h4>Face detected and ready</h4>
                        <p>The system will automatically capture and register as soon as it's ready</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="status-processing">
                    <div class="status-icon"></div>
                    <div class="status-text">
                        <h4>Detecting face...</h4>
                        <p>Please place your face within the camera frame and wait for the system to be ready</p>
                    </div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.session_state.get('reg_ready', False) and not st.session_state.get('reg_best_bytes'):
            st.markdown("""
            <div class="capture-actions">
                <h4>Ready for photo capture</h4>
                <p>The system will automatically capture and register as soon as a suitable face is detected</p>
            </div>
            """, unsafe_allow_html=True)
        
        if st.session_state.get('reg_best_bytes'):
            st.markdown("""
            <div class="capture-success">
                <h4>Face photo captured successfully!</h4>
                <p>You can submit the registration form now</p>
            </div>
            """, unsafe_allow_html=True)
            
            import io
            from PIL import Image
            img_bytes = st.session_state.reg_best_bytes
            img = Image.open(io.BytesIO(img_bytes))
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(img, caption="Captured Face Image", use_container_width=True)
    else:
        st.markdown("""
        <div class="camera-error">
            <h4>Camera not detected</h4>
            <p>Please check camera access permissions and try again</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("Ensure camera access is allowed when prompted by the browser.")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Retry Camera", width='stretch', key="retry_camera_1"):
                st.rerun()
        
        with col2:
            if st.button("Stop Camera", width='stretch', key="stop_camera_2"):
                st.session_state.start_camera = False
                st.rerun()
        
        with col3:
            if st.button("Reset Timer", width='stretch', key="reset_timer_2"):
                st.session_state.timer_reset_requested = True
                st.rerun()
        
        with col4:
            if st.button("Start Timer", width='stretch', key="start_timer_2"):
                st.session_state.timer_start_requested = True
                st.rerun()

def render_quality_meter(ctx_reg):
    pass

def process_auto_capture(ctx_reg):
    if not ctx_reg or not ctx_reg.state.playing:
        return
    
    processor = ctx_reg.video_processor
    if not processor:
        return
    
    ready_for_capture = processor.is_ready_for_capture()
    timer_expired = getattr(processor, 'timer_expired', False)
    best_frame = getattr(processor, 'best_frame', None)
    capturing_best_frame = getattr(processor, 'capturing_best_frame', False)
    capture_remaining = getattr(processor, 'capture_remaining', 0.0)
    
    logger.info(f"Ready for capture: {ready_for_capture}")
    
    current_state = determine_capture_state(ready_for_capture, timer_expired, best_frame, capturing_best_frame)
    
    logger.info(f"Debug - ready_for_capture: {ready_for_capture}, timer_expired: {timer_expired}")
    logger.info(f"Debug - best_frame: {best_frame is not None}, capturing_best_frame: {capturing_best_frame}")
    logger.info(f"Debug - reg_ready: {st.session_state.get('reg_ready', False)}, reg_best_bytes: {st.session_state.get('reg_best_bytes') is not None}")
    logger.info(f"Debug - current_state: {current_state}")
    
    switch_cases = {
        'FIRST_READY': handle_first_ready_state,
        'BEST_FRAME_CAPTURED': handle_best_frame_captured_state,
        'TIMER_EXPIRED': handle_timer_expired_state,
        'CAPTURING_BEST_FRAME': handle_capturing_best_frame_state,
        'PROCESSING': handle_processing_state
    }
    
    handler = switch_cases.get(current_state, handle_processing_state)
    handler(processor, ctx_reg, capture_remaining)
    
    auto_refresh_ui()

def determine_capture_state(ready_for_capture, timer_expired, best_frame, capturing_best_frame):
    logger.info(f"determine_capture_state - ready_for_capture: {ready_for_capture}, timer_expired: {timer_expired}")
    logger.info(f"determine_capture_state - best_frame: {best_frame is not None}, capturing_best_frame: {capturing_best_frame}")
    logger.info(f"determine_capture_state - reg_ready: {st.session_state.get('reg_ready', False)}, reg_best_bytes: {st.session_state.get('reg_best_bytes') is not None}")
    
    if timer_expired and not st.session_state.get('reg_ready', False):
        return 'TIMER_EXPIRED'
    elif ready_for_capture and best_frame is not None and not st.session_state.get('reg_best_bytes'):
        return 'BEST_FRAME_CAPTURED'
    elif ready_for_capture and capturing_best_frame:
        return 'CAPTURING_BEST_FRAME'
    elif ready_for_capture and not st.session_state.get('reg_ready', False):
        return 'FIRST_READY'
    else:
        return 'PROCESSING'

def handle_first_ready_state(processor, ctx_reg, capture_remaining):
    st.session_state.reg_ready = True
    st.markdown("""
    <div class="status-ready">
        <div class="status-icon"></div>
        <div class="status-text">
            <h4>Face detected and ready!</h4>
            <p>Status has turned GREEN - The system will automatically capture and register now</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def handle_best_frame_captured_state(processor, ctx_reg, capture_remaining):
    best_frame = getattr(processor, 'best_frame', None)
    _, buffer = cv2.imencode('.jpg', best_frame)
    frame_bytes = buffer.tobytes()
    st.session_state.reg_best_bytes = frame_bytes

    st.markdown("""
    <div class="capture-success">
        <h4>Face photo captured successfully!</h4>
        <p>Status changed from red to green within the allowed time</p>
        <p>Processing and registering student...</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(best_frame, caption="Captured Face Image", use_container_width=True)

    st.info("Registering student...")
    
    if not st.session_state.get('reg_auto_submitted', False):
        st.session_state.reg_auto_submitted = True
        handle_registration_submission()
        st.rerun()

def handle_timer_expired_state(processor, ctx_reg, capture_remaining):
    status_text = getattr(processor, 'status_text', 'Scan time expired!')
    hint_text = getattr(processor, 'hint', 'Please try again under better conditions.')

    st.error(f"{status_text}")
    st.warning(f"{hint_text}")

    st.info("Form has been reset. Camera continues to run for the next person.")

    reset_registration_states()
    st.session_state.reg_ready = False
    st.session_state.start_camera = True

def handle_capturing_best_frame_state(processor, ctx_reg, capture_remaining):
    st.markdown(f"""
    <div style="background: #d4edda; border: 2px solid #28a745; padding: 15px; margin: 10px 0; border-radius: 8px; text-align: center;">
        <h3 style="color: #155724; margin: 0;">AUTOMATIC CAPTURE!</h3>
        <p style="color: #155724; margin: 5px 0; font-size: 18px;">The system is automatically capturing the best image - Hold still</p>
        <p style="color: #155724; margin: 0; font-weight: bold;">Time remaining: {capture_remaining:.1f}s</p>
    </div>
    """, unsafe_allow_html=True)
    
    best_frame = getattr(processor, 'best_frame', None)
    if best_frame is not None and not st.session_state.get('reg_best_bytes'):
        logger.info("Best frame captured during capture process - switching to BEST_FRAME_CAPTURED")
        handle_best_frame_captured_state(processor, ctx_reg, capture_remaining)
        return
    
    debug_info = get_debug_info(processor)
    st.markdown(debug_info, unsafe_allow_html=True)

def handle_processing_state(processor, ctx_reg, capture_remaining):
    timer_expired = getattr(processor, 'timer_expired', False)
    if timer_expired and not st.session_state.get('reg_ready', False):
        status_text = getattr(processor, 'status_text', 'Scan time expired!')
        hint_text = getattr(processor, 'hint', 'Please try again under better conditions.')
        
        st.error(f"{status_text}")
        st.warning(f"{hint_text}")
        
        st.info("Form has been reset. Camera continues to run for the next person.")
        
        reset_registration_states()
        st.session_state.reg_ready = False
        st.session_state.start_camera = True
        return
        
    if not st.session_state.get('reg_ready', False):
        timer_active = processor.is_timer_active()
        remaining_time = processor.get_remaining_time()
        color_status = getattr(processor, 'color_status', 'red')
        
        capturing_best_frame = False
        if timer_active:
            capturing_best_frame = getattr(processor, 'is_capturing_best_frame', lambda: False)()
            if capturing_best_frame:
                capture_remaining = getattr(processor, 'get_best_frame_remaining_time', lambda: 0)()
                timer_text = f"Timer: {remaining_time:.1f}s | Capture: {capture_remaining:.1f}s - AUTOMATIC CAPTURE!"
                timer_color = "green"
                status_icon = ""
            else:
                check_timer_active = getattr(processor, 'is_check_timer_active', lambda: False)()
                if check_timer_active:
                    check_remaining = getattr(processor, 'get_check_remaining_time', lambda: 0)()
                    timer_text = f"Timer: {remaining_time:.1f}s | Check: {check_remaining:.2f}s"
                    timer_color = "green" if check_remaining > 0.4 else "red"
                    status_icon = ""
                else:
                    timer_text = f"Timer: {remaining_time:.1f}s | Check: Waiting for face"
                    timer_color = "orange"
                    status_icon = ""
        elif getattr(processor, 'timer_expired', False):
            timer_text = "Timer: TIME EXPIRED!"
            timer_color = "red"
            status_icon = ""
        else:
            timer_text = "Timer: Not started"
            timer_color = "gray"
            status_icon = ""
        
        readiness = getattr(processor, 'readiness', 0)
        liveness_ok = getattr(processor, 'liveness_ok', False)
        face_ok = getattr(processor, 'face_ok', False)
        no_mask = not getattr(processor, 'mask_suspect', True)
        
        status_indicators = []
        if face_ok:
            status_indicators.append("Face OK")
        else:
            status_indicators.append("Face NOT OK")
            
        if liveness_ok:
            status_indicators.append("Liveness OK")
        else:
            status_indicators.append("Liveness NOT OK")
            
        if no_mask:
            status_indicators.append("No Mask")
        else:
            status_indicators.append("Mask Detected")
        
        status_text = " | ".join(status_indicators)
        
        debug_info = f"""
        <div style="background: #e8f4fd; padding: 12px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #2196F3;">
            <div style="font-weight: bold; color: #1976D2; margin-bottom: 8px;">System Status</div>
            <div style="font-size: 14px; color: #424242;">{status_text}</div>
            <div style="font-size: 12px; color: #666; margin-top: 4px;">
                Quality: {readiness:.1%} | Time Remaining: {remaining_time:.1f}s
            </div>
        </div>
        """
        
        if color_status == "green":
            status_bg = "#d4edda"
            status_border = "#28a745"
            status_text_color = "#155724"
        elif color_status == "yellow":
            status_bg = "#fff3cd"
            status_border = "#ffc107"
            status_text_color = "#856404"
        else:
            status_bg = "#f8d7da"
            status_border = "#dc3545"
            status_text_color = "#721c24"
        
        st.markdown(f"""
        <div style="background: {status_bg}; border: 2px solid {status_border}; padding: 20px; margin: 15px 0; border-radius: 12px;">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="font-size: 24px; margin-right: 12px;">{status_icon}</div>
                <div>
                    <h3 style="margin: 0; color: {status_text_color}; font-size: 18px;">Detecting face...</h3>
                    <p style="margin: 5px 0 0 0; color: {status_text_color}; font-size: 14px;">Please place your face within the camera frame and wait for the system to be ready</p>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.7); padding: 12px; border-radius: 8px; margin-bottom: 10px;">
                <div style="color: {status_text_color}; font-weight: bold; font-size: 16px; text-align: center;">{timer_text}</div>
                <div style="color: {status_text_color}; font-size: 14px; text-align: center; margin-top: 5px;">
                    Status: <strong>{color_status.upper()}</strong>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(debug_info, unsafe_allow_html=True)

def get_debug_info(processor):
    timer_active = processor.is_timer_active()
    remaining_time = processor.get_remaining_time()
    color_status = getattr(processor, 'color_status', 'red')
    
    capturing_best_frame = False
    if timer_active:
        capturing_best_frame = getattr(processor, 'is_capturing_best_frame', lambda: False)()
        if capturing_best_frame:
            capture_remaining = getattr(processor, 'get_best_frame_remaining_time', lambda: 0)()
            timer_text = f"Timer: {remaining_time:.1f}s | Capture: {capture_remaining:.1f}s - AUTOMATIC CAPTURE!"
        else:
            check_timer_active = getattr(processor, 'is_check_timer_active', lambda: False)()
            if check_timer_active:
                check_remaining = getattr(processor, 'get_check_remaining_time', lambda: 0)()
                timer_text = f"Timer: {remaining_time:.1f}s | Check: {check_remaining:.2f}s"
            else:
                timer_text = f"Timer: {remaining_time:.1f}s | Check: Waiting for face"
    elif getattr(processor, 'timer_expired', False):
        timer_text = "Timer: TIME EXPIRED!"
    else:
        timer_text = "Timer: Not started"
    
    readiness = getattr(processor, 'readiness', 0)
    liveness_ok = getattr(processor, 'liveness_ok', False)
    face_ok = getattr(processor, 'face_ok', False)
    no_mask = not getattr(processor, 'mask_suspect', True)
    
    status_indicators = []
    if face_ok:
        status_indicators.append("Face OK")
    else:
        status_indicators.append("Face NOT OK")
        
    if liveness_ok:
        status_indicators.append("Liveness OK")
    else:
        status_indicators.append("Liveness NOT OK")
        
    if no_mask:
        status_indicators.append("No Mask")
    else:
        status_indicators.append("Mask Detected")
    
    status_text = " | ".join(status_indicators)
    
    return f"""
    <div style="background: #e8f4fd; padding: 12px; margin: 10px 0; border-radius: 8px; border-left: 44px solid #2196F3;">
        <div style="font-weight: bold; color: #1976D2; margin-bottom: 8px;">System Status</div>
        <div style="font-size: 14px; color: #424242;">{status_text}</div>
        <div style="font-size: 12px; color: #666; margin-top: 4px;">
            Quality: {readiness:.1%} | Time Remaining: {remaining_time:.1f}s
        </div>
    </div>
    """

def handle_registration_submission():
    form_data = st.session_state.get('registration_data', {})
    
    face_bytes = st.session_state.get('reg_best_bytes') or st.session_state.get('photo_bytes')
    
    import time
    timestamp = int(time.time())
    form_data['student_id'] = f"SV{timestamp % 100000:05d}"
    
    required_fields = ['full_name', 'username']
    field_names = {
        'student_id': 'Student ID',
        'full_name': 'Full Name',
        'class_name': 'Class Name',
        'username': 'Username',
        'email': 'E-mail'
    }
    missing_fields = [field for field in required_fields if not form_data.get(field)]
    
    if missing_fields:
        missing_names = [field_names[field] for field in missing_fields]
        st.error(f"Please fill in all required fields: {', '.join(missing_names)}")
        return
    
    email = form_data.get('email', '')
    if email and '@' not in email:
        st.error("Invalid email address")
        return
    
    if not face_bytes:
        st.error("Please capture a face photo before submitting")
        return
    
    with st.spinner("Registering student..."):
        try:
            response = api_controller.register_student(form_data, face_bytes)
            
            if response.get('success'):
                st.success("Student registration successful!")
                
                student_info = response.get('student', {})
                st.markdown(f"""
                <div class="success-card">
                    <h4 style="margin: 0 0 10px 0; color: #28a745;">Registration Successful</h4>
                    <p><strong>Student ID:</strong> {student_info.get('student_id', 'N/A')}</p>
                    <p><strong>Full Name:</strong> {student_info.get('full_name', 'N/A')}</p>
                    <p><strong>Class Name:</strong> {student_info.get('class_name', 'N/A')}</p>
                    <p><strong>Username:</strong> {student_info.get('username', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.success("Registration successful! Form has been reset, ready for the next person.")
                
                reset_registration_states()
                st.session_state.reg_ready = False
                st.session_state.start_camera = True
                st.session_state.registration_data = {}
                
                # Add delay before rerun to show notification
                time.sleep(4)  # 4 second delay
                st.rerun()
            else:
                error_code = response.get('error', 'UNKNOWN_ERROR')
                error_msg = response.get('message', 'Registration failed')
                
                if error_code == 'USERNAME_EXISTS':
                    st.error("Username already exists. Please choose a different username.")
                elif error_code == 'DUPLICATE_FACE':
                    st.error("This face has already been registered in the system.")
                elif error_code == 'FACE_MASK_DETECTED':
                    st.error("Face mask detected. Please remove your mask and try again.")
                elif error_code == 'ENCODE_ERROR':
                    st.error("Face processing error. Please retake the photo with better quality.")
                elif error_code == 'MISSING_FIELDS':
                    st.error("Missing required information. Please check the form again.")
                else:
                    st.error(f"Registration failed: {error_msg}")
                
                st.warning("Registration failed! Form has been reset, ready for the next person.")
                
                reset_registration_states()
                st.session_state.reg_ready = False
                st.session_state.start_camera = True
                st.session_state.registration_data = {}
                
                # Add delay before rerun to show notification
                time.sleep(4)  # 4 second delay
                st.rerun()
                
        except Exception as e:
            error_str = str(e)
            if "Face mask detected" in error_str:
                st.error("Face mask detected. Please remove your mask and try again.")
            elif "Face encoding failed" in error_str:
                st.error("Face processing error. Please retake the photo with better quality.")
            else:
                st.error(f"Registration error: {error_str}")
            
            st.error("Form has been reset, ready for the next person.")
            
            reset_registration_states()
            st.session_state.reg_ready = False
            st.session_state.start_camera = True
            logger.error(f"Registration error: {str(e)}")
            
            # Add delay before rerun to show notification
            time.sleep(4)  # 4 second delay
            st.rerun()
