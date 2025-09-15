import streamlit as st
from datetime import datetime

def get_status_messages(continuous_mode=True):
    return {
        'not_started': "Welcome! Scan your face to start attendance.",
        'checked_in': "Checked In! Scan again to Check Out.",
        'checked_out': "Complete! Ready for the next student..." if continuous_mode else "Complete! You have been marked present today.",
        'completed': "This student has completed attendance. Ready for the next person..." if continuous_mode else "You have completed attendance for today!"
    }

def get_attendance_actions():
    return {
        'not_started': 'checkin',
        'checked_in': 'checkout',
        'checked_out': 'completed',
        'completed': 'completed'
    }

def get_next_actions():
    return {
        'checked_in': ("The next scan will be Check Out", 'info'),
        'checked_out': ("Complete! You have been marked present today.", 'success'),
        'completed': ("You have completed attendance for today!", 'warning')
    }

def get_error_messages():
    return {
        'STUDENT_NOT_FOUND': "Student not found in the system.",
        'FACE_NOT_RECOGNIZED': "Face not recognized. Please try again.",
        'FACE_MASK_DETECTED': "Face mask detected. Please remove your mask and try again.",
        'ENCODE_ERROR': "Face processing error. Please capture a better quality image."
    }

def get_exception_messages():
    return {
        "Face mask detected": "Face mask detected. Please remove your mask and try again.",
        "Face encoding failed": "Face processing error. Please capture a better quality image."
    }

def get_timer_configs(remaining_time, processor):
    return {
        'capturing': {
            'text': f"Timer: {remaining_time:.1f}s | Capture: {getattr(processor, 'get_best_frame_remaining_time', lambda: 0)():.1f}s - AUTO CAPTURE!",
            'color': "green",
            'icon': ""
        },
        'checking': {
            'text': f"Timer: {remaining_time:.1f}s | Check: {getattr(processor, 'get_check_remaining_time', lambda: 0)():.2f}s",
            'color': "green" if getattr(processor, 'get_check_remaining_time', lambda: 0)() > 0.4 else "red",
            'icon': ""
        },
        'waiting': {
            'text': f"Timer: {remaining_time:.1f}s | Check: Waiting for face",
            'color': "orange",
            'icon': ""
        },
        'expired': {
            'text': "Timer: TIME EXPIRED!",
            'color': "red",
            'icon': ""
        },
        'inactive': {
            'text': "Timer: Not started",
            'color': "gray",
            'icon': ""
        }
    }

def get_color_configs():
    return {
        "green": {
            "bg": "#d4edda",
            "border": "#28a745",
            "text": "#155724"
        },
        "yellow": {
            "bg": "#fff3cd",
            "border": "#ffc107",
            "text": "#856404"
        },
        "default": {
            "bg": "#f8d7da",
            "border": "#dc3545",
            "text": "#721c24"
        }
    }

def get_continuous_actions():
    return {
        'checked_out': {
            'message': "Ready for the next student...",
            'message_type': 'info',
            'reset_status': True
        },
        'completed': {
            'message': "This student has completed attendance. Ready for the next person...",
            'message_type': 'warning',
            'reset_status': True
        },
        'default': {
            'message': "Continuing with the current student...",
            'message_type': 'info',
            'reset_status': False
        }
    }

def get_status_updates():
    return {
        'checkin': {
            'not_started': ('checked_in', 1),
            'default': ('current_status', 'scan_count + 1')
        },
        'checkout': {
            'checked_in': ('checked_out', 2),
            'default': ('current_status', 'scan_count + 1')
        },
        'completed': {
            'default': ('completed', 'scan_count + 1')
        }
    }

def check_time_restriction(student_id):
    last_scan_times = st.session_state.get('last_scan_times', {})
    current_time = datetime.now()
    
    if student_id in last_scan_times:
        last_scan_time = last_scan_times[student_id]
        time_diff = current_time - last_scan_time
        hours_diff = time_diff.total_seconds() / 3600
        
        if hours_diff < 3:
            remaining_hours = 3 - hours_diff
            remaining_minutes = int(remaining_hours * 60)
            return False, f"You need to wait {remaining_minutes} more minutes to scan again (minimum 3 hours)"
    
    return True, None

def determine_attendance_action():
    status = st.session_state.get('attendance_status', 'not_started')
    action_map = get_attendance_actions()
    return action_map.get(status, 'checkin')

def update_attendance_status(attendance_type):
    current_status = st.session_state.get('attendance_status', 'not_started')
    scan_count = st.session_state.get('attendance_scan_count', 0)
    current_student = st.session_state.get('current_student_id')
    
    status_updates = get_status_updates()
    update_rule = status_updates.get(attendance_type, {})
    
    if current_status in update_rule:
        new_status, new_count = update_rule[current_status]
    else:
        default_rule = update_rule.get('default', (current_status, scan_count + 1))
        if default_rule[0] == 'current_status':
            new_status = current_status
        else:
            new_status = default_rule[0]
        
        if default_rule[1] == 'scan_count + 1':
            new_count = scan_count + 1
        else:
            new_count = default_rule[1]
    
    st.session_state.attendance_status = new_status
    st.session_state.attendance_scan_count = new_count
    
    if current_student:
        st.session_state.last_scan_times[current_student] = datetime.now()
