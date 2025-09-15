import streamlit as st
import time
import logging
from datetime import datetime
from controllers.api_controller import api_controller
from utils.attendance_utils import (
    get_error_messages, get_exception_messages, check_time_restriction,
    determine_attendance_action, update_attendance_status
)
from utils.camera_utils import reset_attendance_states

logger = logging.getLogger(__name__)

def handle_attendance_submission():
    face_bytes = st.session_state.get('att_best_bytes')
    
    if not face_bytes:
        st.error("Please capture a face image before submitting attendance")
        return
    
    attendance_type = determine_attendance_action()
    
    with st.spinner("Submitting student attendance..."):
        try:
            if attendance_type == "checkin":
                response = api_controller.checkin_student(face_bytes)
            elif attendance_type == "checkout":
                response = api_controller.checkout_student(face_bytes)
            else:
                st.warning("Invalid attendance status!")
                return
            
            if response.get('success'):
                handle_successful_attendance(response, attendance_type)
            else:
                handle_failed_attendance(response)
                
        except Exception as e:
            handle_attendance_exception(e)
        finally:
            auto_continue_workflow()

def handle_successful_attendance(response, attendance_type):
    student_info = response.get('student', {})
    student_id = student_info.get('student_id', 'N/A')
    
    can_scan, time_warning = check_time_restriction(student_id)
    if not can_scan:
        st.warning(time_warning)
        return
    
    current_student = st.session_state.get('current_student_id')
    if current_student and current_student != student_id:
        st.session_state.attendance_status = 'not_started'
        st.session_state.attendance_scan_count = 0
        st.info(f"New student detected: {student_info.get('full_name', 'N/A')}")
    
    st.session_state.current_student_id = student_id
    
    update_attendance_status(attendance_type)
    
    action_text = "checked in" if attendance_type == "checkin" else "checked out"
    
    # Store success info in session state for persistent display
    st.session_state.attendance_success = {
        'student_id': student_id,
        'student_name': student_info.get('full_name', 'N/A'),
        'action': action_text,
        'timestamp': time.time()
    }
    
    # Show success notification with better styling
    st.success(f"Successfully {action_text}!")
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #28a745, #20c997); 
                color: white; padding: 20px; border-radius: 12px; 
                margin: 15px 0; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
                border-left: 5px solid #155724; animation: slideIn 0.5s ease-out;">
        <h4 style="margin: 0 0 15px 0; color: white; font-size: 1.3em;">
            Attendance Recorded
        </h4>
        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
            <p style="margin: 5px 0;"><strong>Student ID:</strong> {student_id}</p>
            <p style="margin: 5px 0;"><strong>Name:</strong> {student_info.get('full_name', 'N/A')}</p>
            <p style="margin: 5px 0;"><strong>Action:</strong> {action_text.title()}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    show_next_action()
    
    # Add delay before rerun to show notification
    time.sleep(4)  # 4 second delay
    

def handle_failed_attendance(response):
    error_code = response.get('error', 'UNKNOWN_ERROR')
    error_msg = response.get('message', 'Attendance submission failed')
    
    # Store error info in session state for persistent display
    st.session_state.attendance_error = {
        'error_code': error_code,
        'error_msg': error_msg,
        'timestamp': time.time()
    }
    
    error_messages = get_error_messages()
    error_message = error_messages.get(error_code, f"Attendance submission failed: {error_msg}")
    
    st.error(error_message)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #dc3545, #c82333); 
                color: white; padding: 20px; border-radius: 12px; 
                margin: 15px 0; box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
                border-left: 5px solid #721c24; animation: slideIn 0.5s ease-out;">
        <h4 style="margin: 0 0 15px 0; color: white; font-size: 1.3em;">
            Attendance Failed
        </h4>
        <p style="margin: 0; color: white; font-size: 1.1em;">{error_message}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add delay before rerun to show notification
    time.sleep(4)  # 4 second delay
    

def handle_attendance_exception(e):
    error_str = str(e)
    
    exception_messages = get_exception_messages()
    
    error_message = None
    for key, message in exception_messages.items():
        if key in error_str:
            error_message = message
            break
    
    if error_message:
        st.error(error_message)
    else:
        st.error(f"Attendance error: {error_str}")
    
    logger.error(f"Attendance error: {str(e)}")
    

def auto_continue_workflow():
    import time
    
    time.sleep(2)
    
    from utils.camera_utils import reset_attendance_states
    reset_attendance_states()
    st.session_state.att_ready = False
    
    
    st.rerun()

def show_next_action():
    from utils.attendance_utils import get_next_actions
    
    current_status = st.session_state.get('attendance_status', 'not_started')
    next_actions = get_next_actions()
    
    if current_status in next_actions:
        message, action_type = next_actions[current_status]
        if action_type == 'info':
            st.info(message)
        elif action_type == 'success':
            st.success(message)
        elif action_type == 'warning':
            st.warning(message)

def handle_continuous_mode():
    from utils.attendance_utils import get_continuous_actions
    from utils.camera_utils import reset_attendance_states
    
    current_status = st.session_state.get('attendance_status', 'not_started')
    continuous_actions = get_continuous_actions()
    
    action = continuous_actions.get(current_status, continuous_actions['default'])
    
    if action['message_type'] == 'info':
        st.info(action['message'])
    elif action['message_type'] == 'warning':
        st.warning(action['message'])
    
    if action['reset_status']:
        st.session_state.attendance_status = 'not_started'
        st.session_state.attendance_scan_count = 0
        st.session_state.current_student_id = None
    
    reset_attendance_states()
    
    st.rerun()
