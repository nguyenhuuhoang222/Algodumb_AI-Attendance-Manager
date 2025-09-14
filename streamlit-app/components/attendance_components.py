"""
Attendance Components - UI components for the attendance interface
"""
import streamlit as st
from utils.attendance_utils import get_status_messages, get_timer_configs, get_color_configs

def render_attendance_status():
    """Displays the current attendance status"""
    status = st.session_state.get('attendance_status', 'not_started')
    scan_count = st.session_state.get('attendance_scan_count', 0)
    current_student = st.session_state.get('current_student_id')
    continuous_mode = st.session_state.get('continuous_mode', True)
    last_scan_times = st.session_state.get('last_scan_times', {})
    
    if current_student:
        st.markdown(f"**Current Student:** {current_student}")
        
        if current_student in last_scan_times:
            from datetime import datetime
            last_scan_time = last_scan_times[current_student]
            time_diff = datetime.now() - last_scan_time
            hours_diff = time_diff.total_seconds() / 3600
            
            if hours_diff < 3:
                remaining_hours = 3 - hours_diff
                remaining_minutes = int(remaining_hours * 60)
                st.warning(f"Last scan: {last_scan_time.strftime('%H:%M:%S')} - Please wait {remaining_minutes} more minutes")
            else:
                st.info(f"Last scan: {last_scan_time.strftime('%H:%M:%S')} - Ready to scan again")
    
    status_messages = get_status_messages(continuous_mode)
    message = status_messages.get(status, "Unknown status")
    
    if status == 'not_started':
        st.info(message)
    elif status == 'checked_in':
        st.success(message)
    elif status == 'checked_out':
        st.success(message)
    elif status == 'completed':
        st.warning(message)
    
    st.caption(f"Scans: {scan_count}")

def render_timer_status(processor, remaining_time, timer_status):
    """Displays the timer status"""
    timer_configs = get_timer_configs(remaining_time, processor)
    timer_config = timer_configs.get(timer_status, timer_configs['inactive'])
    
    return timer_config['text'], timer_config['color']

def render_status_indicators(processor):
    """Displays status indicators"""
    readiness = getattr(processor, 'readiness', 0)
    liveness_ok = getattr(processor, 'liveness_ok', False)
    face_ok = getattr(processor, 'face_ok', False)
    no_mask = not getattr(processor, 'mask_suspect', True)
    
    status_indicators = []
    if face_ok:
        status_indicators.append("Face OK")
    else:
        status_indicators.append("Face Missing")
        
    if liveness_ok:
        status_indicators.append("Liveness OK")
    else:
        status_indicators.append("Liveness Failed")
        
    if no_mask:
        status_indicators.append("No Mask")
    else:
        status_indicators.append("Mask Detected")
    
    return " | ".join(status_indicators), readiness

def render_color_status(color_status):
    """Displays color status"""
    color_configs = get_color_configs()
    color_config = color_configs.get(color_status, color_configs['default'])
    return color_config['bg'], color_config['border'], color_config['text']

def render_camera_controls():
    """Displays camera control buttons"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Restart Camera", width='stretch', key="restart_camera_1"):
            st.session_state.form_reset_counter = st.session_state.get('form_reset_counter', 0) + 1
            st.session_state.start_camera = True
            st.rerun()
    
    with col2:
        if st.button("Stop Camera", width='stretch', key="stop_camera_1"):
            st.session_state.start_camera = False
            st.rerun()
    
    with col3:
        if st.button("Reset Timer", width='stretch', key="reset_timer_1"):
            st.session_state.timer_reset_requested = True
            st.rerun()
    
    with col4:
        if st.button("Start Timer", width='stretch', key="start_timer_1"):
            st.session_state.timer_start_requested = True
            st.rerun()

def render_auto_camera_instructions():
    """Displays automatic camera instructions"""
    st.markdown("""
    <div class="auto-camera-instructions">
        <div class="instruction-header">
            <h4>Automatic Face Scan Instructions (5s + 0.8s Timer)</h4>
        </div>
        <div class="instruction-list">
            <div class="instruction-item">
                <span class="instruction-icon"></span>
                <span>Place your face within the camera frame</span>
            </div>
            <div class="instruction-item">
                <span class="instruction-icon"></span>
                <span>A 5-second timer will start when a face is detected</span>
            </div>
            <div class="instruction-item">
                <span class="instruction-icon"></span>
                <span>A 0.8-second check timer will verify red/green status</span>
            </div>
            <div class="instruction-item">
                <span class="instruction-icon"></span>
                <span>Wait for the status to change from red to green within 0.8s</span>
            </div>
            <div class="instruction-item">
                <span class="instruction-icon"></span>
                <span>Once green, hold still - the system will automatically capture the best image</span>
            </div>
            <div class="instruction-item">
                <span class="instruction-icon"></span>
                <span>Ensure good and clear lighting</span>
            </div>
            <div class="instruction-item">
                <span class="instruction-icon"></span>
                <span>Look directly at the camera</span>
            </div>
            <div class="instruction-item">
                <span class="instruction-icon"></span>
                <span>Remove masks and sunglasses</span>
            </div>
            <div class="instruction-item">
                <span class="instruction-icon"></span>
                <span>When green within 0.8s, the system will automatically capture and record attendance</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_attendance_help():
    """Displays the attendance help section"""
    with st.expander("Attendance Help"):
        st.markdown("""
        ### How to Mark Attendance:
        
        1. **Position your face in the camera** - Ensure good lighting and clear visibility
        2. **Wait for the green border** - The system will automatically detect when ready
        3. **Your face will be recognized** - The system will identify you and record attendance
        4. **Confirmation** - You will see a message confirming successful attendance
        
        ### Tips for Better Recognition:
        - Use good lighting (avoid shadows)
        - Look directly at the camera
        - Remove glasses, masks, or hats
        - Ensure your face is clearly visible
        - Remain still during recognition
        
        ### Troubleshooting:
        - If no face is detected, adjust the lighting
        - If quality is low, move closer to the camera
        - If recognition fails, please try again
        - If a mask is detected, remove any face coverings
        
        ### Attendance Types:
        - **Check In**: Records arrival time
        - **Check Out**: Records departure time
        - **Completed**: Both arrival and departure times are recorded
        """)
