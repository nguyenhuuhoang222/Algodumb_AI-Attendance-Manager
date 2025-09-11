import streamlit as st
from utils import repo
import math
import pandas as pd

st.set_page_config(page_title="Users Management", page_icon="👤", layout="wide")
st.title("Users Management")

PAGE_SIZE = 5

# ---------- Create new user ----------
with st.expander("Add User", expanded=False):
    with st.form("create_user_form", clear_on_submit=True):
        name  = st.text_input("Name")
        email = st.text_input("Email")
        image = st.text_input("Image (URL/path)")
        colA, colB = st.columns([1, 2])
        with colA:
            submitted = st.form_submit_button("Create")
        with colB:
            if image:
                st.image(image, caption="Preview", width=200, use_container_width=False)
        if submitted:
            if not name:
                st.error("Name is required.")
            else:
                res = repo.create_user({"name": name, "email": email, "image_path": image})
                st.success("User created (mock if API not ready).")
                st.json(res)

st.divider()

# ---------- Filters ----------
left, mid = st.columns([4, 2])
with left:
    q = st.text_input("Search by name", value=st.session_state.get("users_q", ""))

# keep page in session (pagination controls are at the bottom)
if "users_page" not in st.session_state:
    st.session_state["users_page"] = 1
page = st.session_state["users_page"]

# apply search 
try:
    items, total = repo.list_users(search=q, page=page, size=PAGE_SIZE)
except TypeError:
    # fallback if repo.list_users doesn't accept 
    items, total = repo.list_users(search=q, page=page, size=PAGE_SIZE)

st.session_state["users_q"] = q

st.divider()

# ---------- List ----------
if not items:
    st.info("No data available.")
else:
    # fields to not repeat in the compact metadata table
    exclude_keys = {
        "image_path", "avatar", "photo_url",
        "id", "name", "email"
    }

    def labelize(k: str) -> str:
        return k.replace("_", " ").title()

    for u in items:
        with st.container(border=True):
            cols = st.columns([1, 3, 3, 3])

            # image (avatar or photo)
            img = u.get("image_path") or u.get("avatar") or u.get("photo_url")
            with cols[0]:
                if img:
                    st.image(img, width=96)

            # basic info
            with cols[1]:
                st.markdown(f"**{u.get('name', '(no name)')}**")
                st.caption(f"User ID: `{u.get('id','n/a')}`")

            # contact
            with cols[2]:
                st.write(u.get("email", ""))

            # compact metadata (no st.json)
            with cols[3]:
                other = {
                    labelize(k): v for k, v in u.items()
                    if k not in exclude_keys and v not in (None, "", [])
                }
                if other:
                    with st.expander("More details"):
                        df = pd.DataFrame(other.items(), columns=["Field", "Value"])
                        # stringify complex values to avoid render issues
                        df["Value"] = df["Value"].apply(
                            lambda v: v if isinstance(v, (int, float)) else str(v)
                        )
                        st.dataframe(
                            df,
                            use_container_width=True,
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
            st.session_state["users_page"] = max(1, page - 1)
            st.rerun()
    with pcol2:
        st.markdown(
            f"<div style='text-align:center;'>Page <b>{page}</b> of <b>{total_pages}</b> · Total <b>{total}</b></div>",
            unsafe_allow_html=True
        )
    with pcol3:
        if st.button("Next", disabled=next_disabled, use_container_width=True):
            st.session_state["users_page"] = min(total_pages, page + 1)
            st.rerun()
