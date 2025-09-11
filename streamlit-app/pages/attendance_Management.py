import streamlit as st
from utils import repo
import math
import pandas as pd

st.set_page_config(page_title="Attendance Management",page_icon="📝", layout="wide")
st.title("Attendance Management")


PAGE_SIZE = 5

# ---------- Filters ----------
left, mid = st.columns([4, 2])
with left:
    q = st.text_input("Search by name", value=st.session_state.get("att_q", ""))
with mid:
    status = st.selectbox("Status", ["", "present", "absent"], index=0)

# keep page in session (pagination controls are at the bottom)
if "att_page" not in st.session_state:
    st.session_state["att_page"] = 1
page = st.session_state["att_page"]

items, total = repo.list_attendance(search=q, status=status, page=page, size=PAGE_SIZE)
st.session_state["att_q"] = q

st.divider()

# ---------- List ----------
if not items:
    st.info("No data available.")
else:
    exclude_keys = {
        "captured_image", "image_path", "photo_url",
        "user_name", "user_id", "timestamp", "status", "note", "id"
    }

    def labelize(k: str) -> str:
        return k.replace("_", " ").title()

    for a in items:
        with st.container(border=True):
            cols = st.columns([1, 3, 2, 2, 2])
            # image (user or captured)
            img = a.get("captured_image") or a.get("image_path") or a.get("photo_url")
            with cols[0]:
                if img:
                    st.image(img, width=96)

            # basic info
            with cols[1]:
                st.markdown(f"**{a.get('user_name', '(unknown)')}**")
                st.caption(f"User ID: `{a.get('user_id','n/a')}` · Record ID: `{a.get('id','n/a')}`")

            # time + note
            with cols[2]:
                st.write(a.get("timestamp", ""))
                note = a.get("note", "")
                if note:
                    st.caption(note)

            # status
            with cols[3]:
                st.markdown(f"**Status:** {a.get('status','')}")

            # compact metadata (no st.json)
            with cols[4]:
                other = {
                    labelize(k): v for k, v in a.items()
                    if k not in exclude_keys and v not in (None, "", [])
                }
                if other:
                    with st.expander("More details"):
                        df = pd.DataFrame(other.items(), columns=["Field", "Value"])
                        # (tùy chọn) chuyển value sang chuỗi để tránh lỗi khi có object/phức tạp
                        df["Value"] = df["Value"].apply(lambda v: v if isinstance(v, (int, float)) else str(v))

                        # DataFrame tương tác: kéo ngang, resize cột, copy; không cần fullscreen
                        st.dataframe(
                        df,
                        use_container_width=True,     # fit theo expander
                        hide_index=True
                    )


    st.divider()

    # ---------- Pagination (bottom) ----------
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    prev_disabled = page <= 1
    next_disabled = page >= total_pages

    pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
    with pcol1:
        if st.button("Previous", disabled=prev_disabled, use_container_width=True):
            st.session_state["att_page"] = max(1, page - 1)
            st.rerun()
    with pcol2:
        st.markdown(
            f"<div style='text-align:center;'>Page <b>{page}</b> of <b>{total_pages}</b> · Total <b>{total}</b></div>",
            unsafe_allow_html=True
        )
    with pcol3:
        if st.button("Next", disabled=next_disabled, use_container_width=True):
            st.session_state["att_page"] = min(total_pages, page + 1)
            st.rerun()
