import streamlit as st
from components.simple_camera import render_simple_camera
from controllers.api_controller import api_controller

def render_camera_test():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2c3e50; margin-bottom: 10px;">Camera Test</h1>
        <p style="color: #7f8c8d; font-size: 16px;">Test camera functionality and face detection</p>
    </div>
    """, unsafe_allow_html=True)
    
    render_simple_camera()
    
    if 'photo_bytes' in st.session_state:
        render_face_detection_test()

def render_face_detection_test():
    st.markdown("### Face Detection Test")
    
    if st.button("Test Face Detection", use_container_width=True):
        with st.spinner("Processing face detection..."):
            try:
                response = api_controller.encode_face_single(st.session_state.photo_bytes)
                
                if response.get('success'):
                    st.success("Face detected and encoded successfully!")
                    
                    if 'face_image' in response:
                        import base64
                        from PIL import Image
                        import io
                        
                        face_image_b64 = response['face_image']
                        face_image_data = base64.b64decode(face_image_b64)
                        face_image = Image.open(io.BytesIO(face_image_data))
                        
                        st.image(face_image, caption="Detected Face", use_column_width=True)
                    
                    embedding = response.get('embedding', '')
                    if embedding:
                        st.info(f"Face embedding generated: {len(embedding)} characters")
                else:
                    error_msg = response.get('message', 'Unknown error')
                    st.error(f"Face detection failed: {error_msg}")
                    
            except Exception as e:
                st.error(f"Face detection error: {str(e)}")
    
    st.markdown("### Service Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Check FaceID Service"):
            try:
                if api_controller.check_faceid_service():
                    st.success("FaceID Service is online")
                else:
                    st.error("FaceID Service is offline")
            except Exception as e:
                st.error(f"Error checking FaceID Service: {str(e)}")
    
    with col2:
        if st.button("Check User Service"):
            try:
                if api_controller.check_user_service():
                    st.success("User Service is online")
                else:
                    st.error("User Service is offline")
            except Exception as e:
                st.error(f"Error checking User Service: {str(e)}")
    
    st.markdown("### Instructions")
    st.markdown("""
    1. **Start Camera** - Click "Start Camera" to initialize your webcam
    2. **Capture Photo** - Click "Capture Photo" to take a picture
    3. **Test Face Detection** - Click "Test Face Detection" to process the photo
    4. **Check Services** - Verify that backend services are running
    
    **Troubleshooting:**
    - If camera doesn't start, check browser permissions
    - If face detection fails, ensure good lighting and clear face visibility
    - If services are offline, start the backend services first
    """)
