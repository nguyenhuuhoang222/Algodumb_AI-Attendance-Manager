# streamlit-app/app.py
import time
import streamlit as st
from utils import repo  # dùng repo thay vì gọi requests trực tiếp

st.set_page_config(page_title="AI Attendance", page_icon="🧭", layout="wide")

def do_logout():
    st.session_state.pop("auth", None)
    st.success("Signed out.")
    st.rerun()

# Header
st.title("AI Attendance")

# Not signed in -> 2 tabs đăng nhập
if "auth" not in st.session_state:
    tab_pwd, tab_face = st.tabs(["🔐 Password", "📷 Face ID"])

    # Password tab
    with tab_pwd:
        st.subheader("Sign in with Username & Password")
        with st.form("login_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                username = st.text_input("Username", placeholder="your.username")
            with c2:
                password = st.text_input("Password", type="password", placeholder="••••••••")

            a1, a2, a3 = st.columns([1, 2, 1])
            with a1:
                submit = st.form_submit_button("Sign in")
            with a3:
                st.caption("Forgot password? (coming soon)")

            if submit:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    with st.spinner("Signing in..."):
                        res = repo.login_password(username, password)
                    if res.get("ok"):
                        data = res["data"]
                        st.session_state["auth"] = {
                            "username": data.get("username") or username,
                            "method": "password",
                            "token": data.get("token"),
                            "profile": data,
                        }
                        st.success("Signed in successfully.")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Login failed"))

    # Face ID tab
    with tab_face:
        st.subheader("Sign in with Face ID")
        st.caption("Tips: Good lighting, keep face centered, remove masks/sunglasses.")
        captured = st.camera_input("Open camera & capture your face")

        left, right = st.columns([1, 2])
        with left:
            btn_face = st.button("Sign in with Face ID", use_container_width=True, disabled=captured is None)
        with right:
            st.caption("If button is disabled, capture an image first.")

        if btn_face:
            if not captured:
                st.error("Please capture an image first.")
            else:
                with st.spinner("Verifying your face..."):
                    res = repo.login_face(captured.getvalue())
                    time.sleep(0.5)
                if res.get("ok"):
                    data = res["data"]
                    st.session_state["auth"] = {
                        "username": data.get("username", "face_user"),
                        "method": "faceid",
                        "token": data.get("token"),
                        "profile": data,
                    }
                    st.success(f"Welcome, {st.session_state['auth']['username']}!")
                    st.rerun()
                else:
                    st.error(res.get("error", "Face authentication failed"))

# Signed in -> menu + quick actions
else:
    auth = st.session_state["auth"]
    l, r = st.columns([3, 1])

    with l:
        st.success(f"Welcome, **{auth.get('username','User')}**! (via **{auth.get('method')}**)")
        st.subheader("Quick Navigation")
        n1, n2, n3 = st.columns(3)
        with n1:
            st.page_link("pages/dashboard.py", label="🏠 Open Dashboard", icon=":material/dashboard:")
        with n2:
            st.page_link("pages/users_Management.py", label="👤 Users Management", icon=":material/group:")
        with n3:
            st.page_link("pages/attendance_Management.py", label="📝 Attendance Management", icon=":material/fact_check:")

        st.divider()
        st.subheader("Quick Attendance (optional)")
        shot = st.camera_input("Capture attendance photo")
        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button("Submit Attendance", disabled=shot is None):
                if not shot:
                    st.error("Please capture a photo first.")
                else:
                    with st.spinner("Submitting attendance..."):
                        res = repo.submit_attendance(shot.getvalue())
                    if res.get("ok"):
                        st.success("Attendance submitted.")
                        st.toast("Attendance recorded.", icon="✅")
                    else:
                        st.error(res.get("error", "Submit failed"))
        with c2:
            st.caption("This posts to `/attendance/checkin` if available in your backend.")

    with r:
        st.subheader("Session")
        st.json(auth, expanded=False)
        st.button("Sign out", on_click=do_logout, type="primary", use_container_width=True)

    st.divider()
    st.caption("© 2025 AI Attendance — Streamlit UI")
