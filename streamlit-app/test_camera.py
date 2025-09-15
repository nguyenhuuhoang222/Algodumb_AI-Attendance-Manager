import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import cv2
import numpy as np
from typing import Tuple, Optional
import av

class SimpleVideoProcessor:
    def __init__(self):
        self.frame_count = 0
    
    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        self.frame_count += 1
        
        # Convert to numpy array
        img = frame.to_ndarray(format="bgr24")
        
        # Add text overlay
        cv2.putText(img, f"Frame: {self.frame_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Convert back to VideoFrame
        return av.VideoFrame.from_ndarray(img, format="bgr24")

def main():
    st.title("Camera Test")
    
    st.info("Testing camera functionality...")
    
    webrtc_ctx = webrtc_streamer(
        key="test_camera",
        mode=WebRtcMode.SENDRECV,
        media_stream_constraints={
            "video": {
                "facingMode": "user",
                "width": {"ideal": 640, "min": 320},
                "height": {"ideal": 480, "min": 240}
            },
            "audio": False
        },
        video_processor_factory=SimpleVideoProcessor,
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
    
    if webrtc_ctx and webrtc_ctx.state.playing:
        st.success("Camera is working!")
    else:
        st.warning("Camera not started. Please check permissions.")

if __name__ == "__main__":
    main()
