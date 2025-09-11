# streamlit-app/pages/dashboard.py
import streamlit as st
import pandas as pd
import altair as alt
from utils import repo

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("Dashboard")

# ---- Load raw attendance data ----
items, _ = repo.list_attendance(page=1, size=100000)
df = pd.DataFrame(items) if items else pd.DataFrame()

# Bail out early if there's no data at all
if df.empty:
    st.info("No data available.")
    st.stop()

# ---- Normalize & keep only present/absent ----
# Ensure 'status' exists as a string Series
if "status" not in df.columns:
    df["status"] = ""
df["status"] = df["status"].astype(str).str.lower()

df = df[df["status"].isin(["present", "absent"])].copy()
if df.empty:
    st.info("No present/absent records to display.")
    st.stop()

# ---- Parse timestamp -> date, weekday, hour ----
def _parse(ts):
    try:
        return pd.to_datetime(ts, utc=True)
    except Exception:
        try:
            return pd.to_datetime(ts)
        except Exception:
            return pd.NaT

if "timestamp" in df.columns:
    df["ts"] = df["timestamp"].apply(_parse)
else:
    df["ts"] = pd.NaT

df["date"] = pd.to_datetime(df["ts"]).dt.date
df["weekday"] = pd.to_datetime(df["ts"]).dt.day_name()
df["hour"] = pd.to_datetime(df["ts"]).dt.hour

# ---- KPIs (present/absent only) ----
total = len(df)
present_cnt = (df["status"] == "present").sum()
absent_cnt  = (df["status"] == "absent").sum()

c1, c2, c3 = st.columns(3)
c1.metric("Total records (P/A)", total)
c2.metric("Present", present_cnt)
c3.metric("Absent", absent_cnt)
st.divider()

# ---- 1) Status distribution (bar) ----
st.subheader("Status distribution (Present vs Absent)")
dist = (
    df["status"]
    .value_counts()
    .reindex(["present", "absent"], fill_value=0)
    .reset_index()
)
dist.columns = ["status", "count"]

bar = alt.Chart(dist).mark_bar().encode(
    x=alt.X("status:N", title="Status"),
    y=alt.Y("count:Q", title="Records"),
    tooltip=["status", "count"]
).properties(height=240, width="container")
st.altair_chart(bar, use_container_width=True)

st.divider()

# ---- 2) Daily trend (stacked area) ----
st.subheader("Daily trend")
trend = (
    df.dropna(subset=["date"])
      .groupby(["date", "status"])
      .size()
      .reset_index(name="count")
)

if trend.empty:
    st.caption("Insufficient timestamp data for daily trend.")
else:
    area = alt.Chart(trend).mark_area().encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("count:Q", stack="normalize", title="Share (%)"),
        color=alt.Color("status:N", title="Status",
                        scale=alt.Scale(domain=["present", "absent"])),
        tooltip=["date:T", "status:N", "count:Q"]
    ).properties(height=260, width="container")
    st.altair_chart(area, use_container_width=True)

st.divider()

# ---- 3) Heatmap by Weekday & Hour (absence rate) ----
st.subheader("Heatmap by Weekday & Hour (absence rate)")
heat_df = df.dropna(subset=["hour"]).copy()

if heat_df.empty:
    st.caption("Insufficient hour/weekday data for heatmap.")
else:
    grp = (
        heat_df.groupby(["weekday", "hour", "status"])
               .size()
               .reset_index(name="count")
    )
    pivot = grp.pivot_table(
        index=["weekday", "hour"],
        columns="status",
        values="count",
        fill_value=0
    ).reset_index()

    if "present" not in pivot.columns:
        pivot["present"] = 0
    if "absent" not in pivot.columns:
        pivot["absent"] = 0

    # Avoid division by zero: replace 0 total with 1 in denominator
    total_counts = (pivot["absent"] + pivot["present"]).replace({0: 1})
    pivot["absent_rate"] = (pivot["absent"] / total_counts).round(3)

    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot["weekday"] = pd.Categorical(pivot["weekday"], categories=order, ordered=True)

    heat = alt.Chart(pivot).mark_rect().encode(
        x=alt.X("hour:O", title="Hour"),
        y=alt.Y("weekday:O", title="Weekday"),
        color=alt.Color("absent_rate:Q", title="Absence rate", scale=alt.Scale(scheme="reds")),
        tooltip=[
            "weekday",
            "hour",
            alt.Tooltip("present:Q", title="Present"),
            alt.Tooltip("absent:Q", title="Absent"),
            alt.Tooltip("absent_rate:Q", title="Absence rate", format=".0%")
        ]
    ).properties(height=280, width="container")
    st.altair_chart(heat, use_container_width=True)

st.divider()

# ---- 4) Top absentees ----
st.subheader("Top absentees")
name_col = "user_name" if "user_name" in df.columns else None
group_cols = ["user_id"] + ([name_col] if name_col else [])

# Guard: if user_id column is missing, show a hint
if "user_id" not in df.columns:
    st.caption("Column 'user_id' not found; cannot compute top absentees.")
else:
    top_abs = (
        df[df["status"] == "absent"]
        .groupby(group_cols)
        .size()
        .reset_index(name="absent_count")
        .sort_values("absent_count", ascending=False)
        .head(10)
    )
    st.dataframe(top_abs, use_container_width=True)
