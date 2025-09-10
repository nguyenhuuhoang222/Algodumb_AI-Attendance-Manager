import streamlit as st
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
