import streamlit as st

def inject_camera_guides():
    st.markdown(
        """
        <style>
        [data-testid="stCameraInput"] {
          position: relative;
        }
        [data-testid="stCameraInput"]::after{
          content: '';
          position: absolute;
          top: 20%;
          bottom: 20%;
          left: 30%;
          right: 30%;
          border: 3px dashed #22c55e;
          border-radius: 12px;
          pointer-events: none;
          box-shadow: 0 0 0 9999px rgba(0,0,0,0.05) inset;
        }
        [data-testid="stCameraInput"]::before{
          content: 'Place face in frame — look straight — sufficient light';
          position: absolute;
          right: 8px; top: 8px;
          background: rgba(0,0,0,0.6);
          color: #fff; font-size: 12px; padding: 4px 8px; border-radius: 6px;
          z-index: 1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def reset_attendance_states():
    attendance_keys = [
        'att_announced', 'att_auto_submitted', 'att_action', 'att_best_bytes',
        'att_meet_gate', 'att_green_consec', 'att_student_info', 'att_timestamp',
        'att_error', 'att_scan_started', 'att_ready', 'att_processed', 'att_processing'
    ]
    
    for key in attendance_keys:
        if key in st.session_state:
            del st.session_state[key]

def reset_attendance_status():
    status_keys = [
        'attendance_scan_count', 'attendance_status', 'current_student_id', 'last_scan_times'
    ]
    
    for key in status_keys:
        if key in st.session_state:
            del st.session_state[key]

def reset_registration_states():
    registration_keys = [
        'reg_ready', 'reg_auto_submitted', 'reg_completed', 'reg_best_bytes',
        'reg_pose_images', 'reg_green_consec', 'reg_frame_ring', 'reg_scan_started',
        'registration_data', 'show_camera', 'start_camera', 'student_id_input',
        'photo_bytes', 'use_simple_camera', 'timer_reset_requested', 
        'timer_start_requested', 'capture_start_requested', 'form_reset_counter'
    ]
    
    for key in registration_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    st.session_state.registration_data = {}
    
    st.session_state.form_reset_counter = st.session_state.get('form_reset_counter', 0) + 1
    
    import time
    timestamp = int(time.time())
    st.session_state.student_id_input = f"SV{timestamp % 100000:05d}"