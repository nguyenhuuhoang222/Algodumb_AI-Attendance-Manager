import streamlit as st
<<<<<<< HEAD
import requests
import io

st.set_page_config(page_title="Face Login Demo", page_icon="👤")

st.title("Đăng ký / Đăng nhập bằng khuôn mặt")

BASE_URL = st.secrets.get("USER_SERVICE_URL", "http://localhost:5002/api")

tab1, tab2 = st.tabs(["Đăng ký", "Đăng nhập"])

with tab1:
    username = st.text_input("Username", key="reg_user")
    file = st.file_uploader("Ảnh khuôn mặt", type=["jpg","jpeg","png"], key="reg_file")
    if st.button("Đăng ký"):
        if not username or not file:
            st.warning("Nhập username và chọn ảnh.")
        else:
            files = {"file": (file.name, file.read(), file.type)}
            data = {"username": username}
            r = requests.post(f"{BASE_URL}/register-face", files=files, data=data)
            if r.ok:
                st.success("Đăng ký thành công!")
            else:
                st.error(r.text)

with tab2:
    username = st.text_input("Username", key="log_user")
    file = st.file_uploader("Ảnh khuôn mặt", type=["jpg","jpeg","png"], key="log_file")
    if st.button("Đăng nhập"):
        if not username or not file:
            st.warning("Nhập username và chọn ảnh.")
        else:
            files = {"file": (file.name, file.read(), file.type)}
            data = {"username": username}
            r = requests.post(f"{BASE_URL}/login-face", files=files, data=data)
            if r.ok:
                res = r.json()
                if res.get("match"):
                    st.success(f"✅ Đăng nhập OK · distance={res.get('distance'):.4f}")
                else:
                    st.error(f"❌ Không khớp · distance={res.get('distance'):.4f}")
            else:
                st.error(r.text)
=======
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from views import (
    render_dashboard,
    render_registration, 
    render_attendance
)
from views.camera_test_view import render_camera_test
from utils.config import AppConfig
from utils.session_manager import SessionManager

config = AppConfig()

st.set_page_config(
    page_title="AI Attendance Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

session_manager = SessionManager()

st.markdown(config.get_css_styles(), unsafe_allow_html=True)

def main():
    
    session_manager.initialize_session()
    
    render_sidebar()
    
    render_main_content()

def render_sidebar():
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #2c3e50; margin: 0; font-size: 24px;">AI Attendance</h1>
        <p style="color: #7f8c8d; margin: 5px 0 0 0; font-size: 14px;">Smart Face Recognition System</p>
    </div>
    """, unsafe_allow_html=True)
    
    menu_items = [
        ("Dashboard", "dashboard"),
        ("Register", "registration"), 
        ("Attendance", "attendance"),
        ("Camera Test", "camera_test")
    ]
    
    current_page = st.session_state.get('current_page', 'dashboard')
    
    for text, page_key in menu_items:
        if current_page == page_key:
            st.sidebar.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 12px 16px; margin: 8px 0; border-radius: 10px; 
                        color: white; font-weight: 600; cursor: pointer;">
                {text}
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.sidebar.button(f"{text}", key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
    

def render_main_content():
    current_page = st.session_state.get('current_page', 'dashboard')
    
    if current_page == 'dashboard':
        render_dashboard()
    elif current_page == 'registration':
        render_registration()
    elif current_page == 'attendance':
        render_attendance()
    elif current_page == 'camera_test':
        render_camera_test()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()
>>>>>>> clean-branch
