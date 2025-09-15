import streamlit as st
from typing import Dict, Any, Optional

class SessionManager:
    
    def __init__(self):
        self.default_states = {
            'current_page': 'dashboard',
            
            'reg_ready': False,
            'reg_auto_submitted': False,
            'reg_completed': False,
            'reg_best_bytes': None,
            'reg_pose_images': {},
            'reg_green_consec': 0,
            'reg_frame_ring': [],
            'reg_scan_started': False,
            'registration_data': None,
            'show_camera': False,
            
            'att_announced': False,
            'att_auto_submitted': False,
            'att_action': None,
            'att_best_bytes': None,
            'att_meet_gate': False,
            'att_green_consec': 0,
            'att_student_info': None,
            'att_timestamp': None,
            'att_error': None,
            'att_scan_started': False,
            
            'dashboard_data': None,
            'last_refresh': None,
            
            'selected_date': None,
            'report_data': None,
            
            'last_error': None,
            'error_count': 0
        }
    
    def initialize_session(self):
        for key, value in self.default_states.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def reset_registration_states(self):
        reg_keys = [k for k in self.default_states.keys() if k.startswith('reg_')]
        for key in reg_keys:
            st.session_state[key] = self.default_states[key]
    
    def reset_attendance_states(self):
        att_keys = [k for k in self.default_states.keys() if k.startswith('att_')]
        for key in att_keys:
            st.session_state[key] = self.default_states[key]
    
    def set_error(self, error_message: str):
        st.session_state.last_error = error_message
        st.session_state.error_count += 1
    
    def clear_error(self):
        st.session_state.last_error = None
        st.session_state.error_count = 0
    
    def get_state(self, key: str, default: Any = None) -> Any:
        return st.session_state.get(key, default)
    
    def set_state(self, key: str, value: Any):
        st.session_state[key] = value
    
    def update_states(self, states: Dict[str, Any]):
        for key, value in states.items():
            st.session_state[key] = value
    
    def has_error(self) -> bool:
        return st.session_state.get('last_error') is not None
    
    def get_error(self) -> Optional[str]:
        return st.session_state.get('last_error')
    
    def increment_counter(self, counter_name: str) -> int:
        current = st.session_state.get(counter_name, 0)
        new_value = current + 1
        st.session_state[counter_name] = new_value
        return new_value
    
    def reset_counter(self, counter_name: str):
        st.session_state[counter_name] = 0
