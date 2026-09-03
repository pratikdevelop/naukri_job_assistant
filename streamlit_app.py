import streamlit as st
import sqlite3
from pathlib import Path
from naukri_assistant.database import JobDB

# -----------------------------
# Page configuration
# -----------------------------

st.set_page_config(
    page_title="Naukri Job Dashboard",
    page_icon="💼",
    layout="wide",
)


# -----------------------------
# Database path
# -----------------------------

DB_PATH = Path("data/jobs.db")
job_db = JobDB(DB_PATH)


# -----------------------------
# Load jobs from SQLite
# -----------------------------

def load_jobs():
    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    jobs = conn.execute(
        """
        SELECT *
        FROM jobs
        ORDER BY match_score DESC, first_seen DESC
        """
    ).fetchall()

    conn.close()

    return jobs


# -----------------------------
# Dashboard UI
# -----------------------------

st.title("💼 Naukri Job Dashboard")

st.write("Jobs collected by your Naukri scanner.")

jobs = load_jobs()


# -----------------------------
# Score statistics
# -----------------------------

score_90 = sum(
    1 for job in jobs
    if job["match_score"] >= 90
)

score_70 = sum(
    1 for job in jobs
    if job["match_score"] >= 70
)

score_50 = sum(
    1 for job in jobs
    if job["match_score"] >= 50
)


# -----------------------------
# Display metrics
# -----------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📋 Total Jobs",
        len(jobs)
    )

with col2:
    st.metric(
        "🔥 90+ Score",
        score_90
    )

with col3:
    st.metric(
        "⭐ 70+ Score",
        score_70
    )

with col4:
    st.metric(
        "✅ 50+ Score",
        score_50
    )


st.divider()


# -----------------------------
# Score filter
# -----------------------------

score_filter = st.selectbox(
    "🎯 Minimum Match Score",
    [
        "All Jobs",
        "90+ Score",
        "70+ Score",
        "50+ Score",
    ],
)


filtered_jobs = jobs


if score_filter == "90+ Score":

    filtered_jobs = [
        job for job in jobs
        if job["match_score"] >= 90
    ]


elif score_filter == "70+ Score":

    filtered_jobs = [
        job for job in jobs
        if job["match_score"] >= 70
    ]


elif score_filter == "50+ Score":

    filtered_jobs = [
        job for job in jobs
        if job["match_score"] >= 50
    ]


# -----------------------------
# Location filter
# -----------------------------

location_filter = st.selectbox(
    "📍 Location",
    [
        "All Locations",
        "Indore",
        "Remote",
    ],
)


if location_filter == "Indore":

    filtered_jobs = [
        job for job in filtered_jobs
        if "indore" in (job["location"] or "").lower()
    ]


elif location_filter == "Remote":

    filtered_jobs = [
        job for job in filtered_jobs
        if "remote" in (job["location"] or "").lower()
    ]


# -----------------------------
# Filter result
# -----------------------------

st.write(
    f"Showing **{len(filtered_jobs)}** jobs"
)


st.divider()

st.subheader("📋 Jobs")


# -----------------------------
# Display jobs
# -----------------------------

# for job in filtered_jobs:

#     st.markdown(
#         f"### {job['job_title']}"
#     )

#     st.write(
#         f"🏢 **Company:** {job['company']}  \n"
#         f"📍 **Location:** {job['location']}  \n"
#         f"⭐ **Match Score:** {job['match_score']}  \n"
#         f"💼 **Experience:** {job['experience']}  \n"
#         f"💰 **Salary:** {job['salary'] or 'Not specified'}"
#     )

#     st.write(
#         f"🛠️ **Skills:** "
#         f"{job['skills'] or 'Not specified'}"
#     )

#     st.divider()


st.subheader("📋 Jobs")

st.write(f"Showing **{len(filtered_jobs)}** jobs")

for job in filtered_jobs:
    st.markdown("---")

    col1, col2 = st.columns([5, 1])

    with col1:
        st.markdown(f"### 💼 {job['job_title']}")

        st.write(
            f"🏢 **Company:** {job['company']}  \n"
            f"📍 **Location:** {job['location'] or 'Not specified'}  \n"
            f"⭐ **Match Score:** {job['match_score']}  \n"
            f"💼 **Experience:** {job['experience'] or 'Not specified'}  \n"
            f"💰 **Salary:** {job['salary'] or 'Not specified'}"
        )

        if job["skills"]:
            st.write(f"🛠️ **Skills:** {job['skills']}")

    with col2:
        st.write("")

        if job["job_url"]:
            st.link_button(
                "🚀 Apply / Review",
                job["job_url"],
                use_container_width=True,
            )
        else:
            st.button(
                "❌ No URL",
                disabled=True,
                use_container_width=True,
            )