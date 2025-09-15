import streamlit as st
import cv2
import numpy as np
import time
import logging
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from components.video_processor import ReadinessProcessor
from components.simple_camera import render_simple_camera
from components.attendance_components import (
    render_attendance_status, render_timer_status, render_status_indicators,
    render_color_status, render_camera_controls, render_auto_camera_instructions
)
from handlers.attendance_handlers import (
    handle_attendance_submission, handle_continuous_mode
)

def auto_refresh_ui():
    if st.session_state.get('start_camera', False):
        time.sleep(0.5)
        st.rerun()
from utils.session_manager import SessionManager
from utils.camera_utils import inject_camera_guides, reset_attendance_states, reset_attendance_status

logger = logging.getLogger(__name__)

def render_attendance():
    st.markdown("""
    <div class="attendance-header">
        <div class="header-content">
            <h1 class="main-title">Automatic Attendance</h1>
            <p class="subtitle">Fully automatic attendance system - Just scan your face</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    session_manager = SessionManager()
    
    if 'attendance_scan_count' not in st.session_state:
        st.session_state.attendance_scan_count = 0
    if 'attendance_status' not in st.session_state:
        st.session_state.attendance_status = 'not_started'
    if 'continuous_mode' not in st.session_state:
        st.session_state.continuous_mode = True
    if 'current_student_id' not in st.session_state:
        st.session_state.current_student_id = None
    if 'last_scan_times' not in st.session_state:
        st.session_state.last_scan_times = {}
    if 'start_camera' not in st.session_state:
        st.session_state.start_camera = True
    
    # Display success notification if exists
    if st.session_state.get('attendance_success'):
        success_data = st.session_state.attendance_success
        current_time = time.time()
        
        # Show notification for 5 seconds
        if current_time - success_data.get('timestamp', 0) < 5:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #28a745, #20c997); 
                        color: white; padding: 20px; border-radius: 12px; 
                        margin: 15px 0; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
                        border-left: 5px solid #155724; animation: slideIn 0.5s ease-out;">
                <h4 style="margin: 0 0 15px 0; color: white; font-size: 1.3em;">
                    Attendance Recorded
                </h4>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                    <p style="margin: 5px 0;"><strong>Student ID:</strong> {success_data.get('student_id', 'N/A')}</p>
                    <p style="margin: 5px 0;"><strong>Name:</strong> {success_data.get('student_name', 'N/A')}</p>
                    <p style="margin: 5px 0;"><strong>Action:</strong> {success_data.get('action', 'N/A').title()}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Clear success notification after 5 seconds
            st.session_state.attendance_success = None
    
    # Display error notification if exists
    if st.session_state.get('attendance_error'):
        error_data = st.session_state.attendance_error
        current_time = time.time()
        
        # Show notification for 5 seconds
        if current_time - error_data.get('timestamp', 0) < 5:
            error_display = error_data.get('error_msg', 'Attendance failed')
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #dc3545, #c82333); 
                        color: white; padding: 20px; border-radius: 12px; 
                        margin: 15px 0; box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
                        border-left: 5px solid #721c24; animation: slideIn 0.5s ease-out;">
                <h4 style="margin: 0 0 15px 0; color: white; font-size: 1.3em;">
                    Attendance Failed
                </h4>
                <p style="margin: 0; color: white; font-size: 1.1em;">{error_display}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Clear error notification after 5 seconds
            st.session_state.attendance_error = None

    st.markdown("### Step 1: Attendance Status")
    render_attendance_status()
    
    st.markdown("### Step 2: Automatic Face Scan")
    
    if st.session_state.get('start_camera', False):
        render_auto_camera_section()
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Start Camera", use_container_width=True, type="primary"):
                st.session_state.start_camera = True
                st.rerun()
        
        with col2:
            if st.button("Restart Camera", use_container_width=True, key="restart_camera_main"):
                st.session_state.form_reset_counter = st.session_state.get('form_reset_counter', 0) + 1
                st.session_state.start_camera = True
                st.rerun()
        
        if st.session_state.get('att_best_bytes') and not st.session_state.get('att_ready', False):
            st.markdown("### Step 3: Process Attendance")
            st.info("Processing image and marking attendance...")
            
            import io
            from PIL import Image
            img_bytes = st.session_state.att_best_bytes
            img = Image.open(io.BytesIO(img_bytes))
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(img, caption="Captured Face Image", use_container_width=True)
            
            handle_attendance_submission()
        
        render_camera_controls()
    

def render_auto_camera_section():
    render_auto_camera_instructions()
    
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
    
    webrtc_key = f"webrtc_auto_attendance_{st.session_state.get('form_reset_counter', 0)}"
    
    if st.session_state.get('start_camera', False):
        st.info("Starting camera... If the camera does not load, please click the 'Restart Camera' button below.")
    
    ctx_att = webrtc_streamer(
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
    
    if ctx_att and ctx_att.state.playing:
        if st.session_state.get('timer_reset_requested', False):
            if hasattr(ctx_att, 'video_processor') and ctx_att.video_processor:
                ctx_att.video_processor.reset_person_timer()
            st.session_state.timer_reset_requested = False
        
        if st.session_state.get('timer_start_requested', False):
            if hasattr(ctx_att, 'video_processor') and ctx_att.video_processor:
                ctx_att.video_processor.start_person_timer()
            st.session_state.timer_start_requested = False
        
        if st.session_state.get('capture_start_requested', False):
            if hasattr(ctx_att, 'video_processor') and ctx_att.video_processor:
                ctx_att.video_processor.start_best_frame_capture()
            st.session_state.capture_start_requested = False
        
        process_auto_capture(ctx_att)
    elif ctx_att and ctx_att.state.playing is False:
        if st.session_state.get('att_best_bytes'):
            st.info("Camera stopped after capturing image. Processing attendance...")
        else:
            processor = getattr(ctx_att, 'video_processor', None)
            if processor and hasattr(processor, 'timer_expired') and processor.timer_expired:
                if hasattr(processor, 'status_text') and "Liveness check failed" in processor.status_text:
                    st.error("**Liveness Check Failed!**")
                    st.error("The system did not detect your movement within 5 seconds.")
                    st.error("**Instructions:** Please move your head slightly or blink to verify liveness.")
                    st.error("Click the 'Restart Camera' button to try again.")
                else:
                    st.warning("**Time's up!**")
            else:
                st.warning("Camera has stopped. Click the button below to restart.")
            
            render_camera_controls()
    else:
        st.warning("Starting camera...")

def process_auto_capture(ctx_att):
    if not ctx_att or not ctx_att.state.playing:
        return
    
    processor = ctx_att.video_processor
    if not processor:
        return
    
    ready_for_capture = processor.is_ready_for_capture()
    logger.info(f"Ready for capture: {ready_for_capture}")
    
    if ready_for_capture:
        if not st.session_state.get('att_ready', False):
            st.session_state.att_ready = True
            st.markdown("""
            <div class="status-ready">
                <div class="status-icon"></div>
                <div class="status-text">
                    <h4>Face detected and ready!</h4>
                    <p>Status has turned GREEN - The system will automatically capture the image and mark attendance now</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        best_frame = getattr(processor, 'best_frame', None)
        if best_frame is not None and not st.session_state.get('att_best_bytes'):
            _, buffer = cv2.imencode('.jpg', best_frame)
            frame_bytes = buffer.tobytes()
            st.session_state.att_best_bytes = frame_bytes
            
            st.markdown("""
            <div class="capture-success">
                <h4>Face image captured successfully!</h4>
                <p>Status changed from red to green within the allowed time</p>
                <p>Processing and marking attendance...</p>
        </div>
        """, unsafe_allow_html=True)
        
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(best_frame, caption="Captured Face Image", use_container_width=True)
            
            st.info("Marking student attendance...")
            handle_attendance_submission()
            
    else:
        timer_expired = getattr(processor, 'timer_expired', False)
        if timer_expired and not st.session_state.get('att_ready', False):
            status_text = getattr(processor, 'status_text', 'Scan time expired!')
            hint_text = getattr(processor, 'hint', 'Please try again with better conditions.')
            
            st.error(f"{status_text}")
            st.warning(f"{hint_text}")
            
            
            from handlers.attendance_handlers import auto_continue_workflow
            auto_continue_workflow()
            return
        
        if not st.session_state.get('att_ready', False):
            render_processing_status(processor)
    
    auto_refresh_ui()

def render_processing_status(processor):
    timer_active = processor.is_timer_active()
    remaining_time = processor.get_remaining_time()
    color_status = getattr(processor, 'color_status', 'red')
    
    capturing_best_frame = False
    timer_status = "inactive"
    
    if timer_active:
        capturing_best_frame = getattr(processor, 'is_capturing_best_frame', lambda: False)()
        if capturing_best_frame:
            timer_status = "capturing"
        else:
            check_timer_active = getattr(processor, 'is_check_timer_active', lambda: False)()
            if check_timer_active:
                timer_status = "checking"
            else:
                timer_status = "waiting"
    elif getattr(processor, 'timer_expired', False):
        timer_status = "expired"
    else:
        timer_status = "inactive"
    
    timer_text, timer_color = render_timer_status(processor, remaining_time, timer_status)
    
    status_text, readiness = render_status_indicators(processor)
    
    debug_info = f"""
    <div style="background: #e8f4fd; padding: 12px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #2196F3;">
        <div style="font-weight: bold; color: #1976D2; margin-bottom: 8px;">System Status</div>
        <div style="font-size: 14px; color: #424242;">{status_text}</div>
        <div style="font-size: 12px; color: #666; margin-top: 4px;">
            Quality: {readiness:.1%} | Time Remaining: {remaining_time:.1f}s
        </div>
    </div>
    """
    
    status_bg, status_border, status_text_color = render_color_status(color_status)
    
    st.markdown(f"""
    <div style="background: {status_bg}; border: 2px solid {status_border}; padding: 20px; margin: 15px 0; border-radius: 12px;">
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <div style="font-size: 24px; margin-right: 12px;"></div>
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
    
    if capturing_best_frame:
        capture_remaining = getattr(processor, 'get_best_frame_remaining_time', lambda: 0)()
        st.markdown(f"""
        <div style="background: #d4edda; border: 2px solid #28a745; padding: 15px; margin: 10px 0; border-radius: 8px; text-align: center;">
            <h3 style="color: #155724; margin: 0;">AUTOMATIC IMAGE CAPTURE!</h3>
            <p style="color: #155724; margin: 5px 0; font-size: 18px;">The system is automatically capturing the best image - Hold still</p>
            <p style="color: #155724; margin: 0; font-weight: bold;">Time remaining: {capture_remaining:.1f}s</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(debug_info, unsafe_allow_html=True)

def render_simple_camera_section(attendance_type):
    st.markdown("### Face Recognition (Simple Camera)")
    
    render_simple_camera()
    
    if 'photo_bytes' in st.session_state:
        st.success("Photo captured! Processing attendance...")
        
        handle_attendance_submission()