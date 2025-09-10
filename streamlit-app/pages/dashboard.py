import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("Dashboard (demo)")
st.write("Ví dụ biểu đồ/ bảng demo.")

df = pd.DataFrame({
    "user": ["alice", "bob", "charlie"],
    "logins": [5, 3, 8]
})
st.dataframe(df)

fig, ax = plt.subplots()
ax.plot(df["user"], df["logins"])
st.pyplot(fig)
