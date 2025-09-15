import streamlit as st
import cv2
import numpy as np
from typing import Optional, Tuple

class SimpleCamera:
    
    def __init__(self):
        self.cap = None
        self.is_initialized = False
    
    def initialize_camera(self) -> bool:
        try:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.is_initialized = True
                return True
            else:
                return False
        except Exception as e:
            st.error(f"Camera initialization failed: {str(e)}")
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        if not self.is_initialized or not self.cap:
            return None
        
        try:
            ret, frame = self.cap.read()
            if ret:
                return frame
            else:
                return None
        except Exception as e:
            st.error(f"Frame capture failed: {str(e)}")
            return None
    
    def release(self):
        if self.cap:
            self.cap.release()
            self.is_initialized = False

def render_simple_camera():
    st.markdown("### Camera Test")
    
    if 'simple_camera' not in st.session_state:
        st.session_state.simple_camera = SimpleCamera()
    
    camera = st.session_state.simple_camera
    
    if not camera.is_initialized:
        if st.button("Start Camera"):
            if camera.initialize_camera():
                st.success("Camera started successfully!")
                st.rerun()
            else:
                st.error("Failed to start camera. Please check camera permissions.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Capture Photo"):
                frame = camera.get_frame()
                if frame is not None:
                    st.session_state.captured_photo = frame
                    st.success("Photo captured!")
                else:
                    st.error("Failed to capture photo")
        
        with col2:
            if st.button("Stop Camera"):
                camera.release()
                st.rerun()
        
        frame = camera.get_frame()
        if frame is not None:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            st.image(frame_rgb, caption="Live Camera Feed", use_container_width=True)
        
        if 'captured_photo' in st.session_state:
            st.markdown("#### Captured Photo")
            captured_rgb = cv2.cvtColor(st.session_state.captured_photo, cv2.COLOR_BGR2RGB)
            st.image(captured_rgb, caption="Captured Photo", use_container_width=True)
            
            _, buffer = cv2.imencode('.jpg', st.session_state.captured_photo)
            photo_bytes = buffer.tobytes()
            st.session_state.photo_bytes = photo_bytes
            
            st.success("Photo ready for processing!")
