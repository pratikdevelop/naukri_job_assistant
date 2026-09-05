import sqlite3
import subprocess
import sys
from pathlib import Path

import streamlit as st
import yaml

from naukri_assistant.database import JobDB


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "jobs.db"
CONFIG_PATH = ROOT / "config.yaml"
MAIN_PATH = ROOT / "main.py"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Naukri Job Assistant",
    page_icon="💼",
    layout="wide",
)


# ============================================================
# LOAD CONFIG
# ============================================================

@st.cache_data
def load_config():

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()

primary_keywords = config.get(
    "keywords",
    {}
).get(
    "primary",
    []
)

secondary_keywords = config.get(
    "keywords",
    {}
).get(
    "secondary",
    []
)

all_keywords = list(
    dict.fromkeys(
        primary_keywords + secondary_keywords
    )
)

all_locations = list(
    dict.fromkeys(
        config.get("locations", [])
    )
)


# ============================================================
# DATABASE
# ============================================================

def load_jobs():

    if not DB_PATH.exists():
        return []

    conn = sqlite3.connect(
        str(DB_PATH)
    )

    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT *
        FROM jobs
        ORDER BY
            match_score DESC,
            first_seen DESC
        """
    ).fetchall()

    conn.close()

    return rows

# ============================================================
# KEYWORD RELEVANCE
# ============================================================

def normalize_text(value):
    return str(value or "").lower().strip()


def job_search_text(job):
    """
    Build one searchable text field from the important job fields.
    """
    return " ".join(
        [
            normalize_text(job["job_title"]),
            normalize_text(job["skills"]),
            normalize_text(job["description"]),
            normalize_text(job["company"]),
        ]
    )


def is_relevant_job(job, keyword):
    """
    Decide whether a job is genuinely relevant to the
    selected keyword.
    """

    if keyword == "All Keywords":
        return True

    title = normalize_text(
        job["job_title"]
    )

    text = job_search_text(job)

    # ========================================================
    # MERN
    # ========================================================

    if keyword in {
        "MERN Developer",
        "MERN Stack Developer",
        "MERN",
    }:

        # Direct MERN mention
        if "mern" in text:
            return True

        # MERN technology combination
        mern_terms = {
            "mongodb": [
                "mongodb",
                "mongo db",
            ],
            "express": [
                "express.js",
                "express js",
                "express",
            ],
            "react": [
                "react.js",
                "react js",
                "react",
            ],
            "node": [
                "node.js",
                "node js",
                "nodejs",
            ],
        }

        matches = 0

        for variants in mern_terms.values():

            if any(
                variant in text
                for variant in variants
            ):
                matches += 1

        # Require at least 3 of the 4 MERN technologies
        return matches >= 3

    # ========================================================
    # NODE.JS
    # ========================================================

    if keyword == "Node.js Developer":

        return any(
            term in text
            for term in [
                "node.js",
                "node js",
                "nodejs",
            ]
        )

    # ========================================================
    # REACT
    # ========================================================

    if keyword == "React.js Developer":

        return any(
            term in text
            for term in [
                "react.js",
                "react js",
                "reactjs",
            ]
        )

    # ========================================================
    # FULL STACK
    # ========================================================

    if keyword == "Full Stack Developer":

        return (
            "full stack" in text
            or "full-stack" in text
            or (
                "frontend" in text
                and "backend" in text
            )
        )

    # ========================================================
    # BACKEND
    # ========================================================

    if keyword == "Backend Developer":

        backend_terms = [
            "backend",
            "back-end",
            "node.js",
            "nodejs",
            "express",
            "django",
            "fastapi",
            "spring boot",
        ]

        return any(
            term in text
            for term in backend_terms
        )

    # ========================================================
    # JAVASCRIPT
    # ========================================================

    if keyword == "JavaScript Developer":

        return any(
            term in text
            for term in [
                "javascript",
                "java script",
                "typescript",
            ]
        )

    # ========================================================
    # AI ENGINEER
    # ========================================================

    if keyword == "AI Engineer":

        return any(
            term in text
            for term in [
                "ai engineer",
                "artificial intelligence",
                "machine learning",
                "generative ai",
                "llm",
                "langchain",
                "openai",
                "gemini",
            ]
        )

    # ========================================================
    # GENERATIVE AI
    # ========================================================

    if keyword == "Generative AI Developer":

        return any(
            term in text
            for term in [
                "generative ai",
                "genai",
                "llm",
                "langchain",
                "openai",
                "gemini",
                "rag",
            ]
        )

    # ========================================================
    # LLM ENGINEER
    # ========================================================

    if keyword == "LLM Engineer":

        return any(
            term in text
            for term in [
                "llm",
                "large language model",
                "langchain",
                "llama",
                "openai",
                "rag",
            ]
        )

    # ========================================================
    # PYTHON
    # ========================================================

    if keyword == "Python Developer":

        return any(
            term in text
            for term in [
                "python",
                "django",
                "flask",
                "fastapi",
            ]
        )

    # ========================================================
    # ANGULAR
    # ========================================================

    if keyword == "Angular Developer":

        return any(
            term in text
            for term in [
                "angular",
                "angular.js",
                "angularjs",
            ]
        )

    # ========================================================
    # FALLBACK
    # ========================================================

    keyword_words = [
        word
        for word in normalize_text(keyword).split()
        if len(word) > 2
    ]

    if not keyword_words:
        return True

    return any(
        word in title or word in text
        for word in keyword_words
    )
# ============================================================
# RUN MAIN.PY
# ============================================================

def run_main_command(command, keyword=None, location=None):

    args = [
        sys.executable,
        str(MAIN_PATH),
        command,
    ]

    if keyword and keyword != "All Keywords":
        args.extend(
            [
                "--keyword",
                keyword,
            ]
        )

    if location and location != "All Locations":
        args.extend(
            [
                "--location",
                location,
            ]
        )

    try:

        result = subprocess.run(
            args,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        return result

    except Exception as exc:

        class FailedResult:
            returncode = 1
            stdout = ""
            stderr = str(exc)

        return FailedResult()


# ============================================================
# LOGIN
# ============================================================

def start_login():

    try:

        if sys.platform.startswith("win32"):

            subprocess.Popen(
                [
                    sys.executable,
                    str(MAIN_PATH),
                    "login",
                ],
                cwd=str(ROOT),
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )

        else:

            subprocess.Popen(
                [
                    sys.executable,
                    str(MAIN_PATH),
                    "login",
                ],
                cwd=str(ROOT),
            )

        st.success(
            "Naukri login window started. "
            "Complete login/OTP/CAPTCHA manually."
        )

    except Exception as exc:

        st.error(
            f"Could not start login: {exc}"
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🎛️ Naukri Controls")

    st.divider()

    st.subheader("🔎 Search")

    selected_keyword = st.selectbox(
        "Job Keyword",
        ["All Keywords"] + all_keywords,
    )

    selected_location = st.selectbox(
        "Location",
        ["All Locations"] + all_locations,
    )

    st.divider()

    st.subheader("🎯 Job Search & Filters")
    st.caption(
    "All selected filters are applied together."
)

    score_filter = st.selectbox(
        "Minimum Match Score",
        [
            "All Jobs",
            "90+ Score",
            "70+ Score",
            "50+ Score",
        ],
    )

    status_filter = st.selectbox(
        "Application Status",
        [
            "All Status",
            "NEW",
            "APPLIED",
            "SKIPPED",
            "FAILED",
        ],
    )

    st.divider()

    st.subheader("⚡ Actions")

    login_button = st.button(
        "🔐 Naukri Login",
        use_container_width=True,
    )

    scan_button = st.button(
        "🔎 Scan Jobs",
        use_container_width=True,
    )

    refresh_button = st.button(
        "🔄 Refresh Latest Jobs",
        use_container_width=True,
        type="primary",
    )


# ============================================================
# LOGIN
# ============================================================

if login_button:

    start_login()


# ============================================================
# CURRENT SEARCH DESCRIPTION
# ============================================================

keyword_text = (
    "All Keywords"
    if selected_keyword == "All Keywords"
    else selected_keyword
)

location_text = (
    "All Locations"
    if selected_location == "All Locations"
    else selected_location
)


# ============================================================
# SCAN
# ============================================================

if scan_button:

    with st.spinner(
        f"Scanning {keyword_text} | {location_text}..."
    ):

        result = run_main_command(
            "scan",
            selected_keyword,
            selected_location,
        )

    if result.returncode == 0:

        st.success(
            "Scan completed successfully."
        )

        if result.stdout:

            with st.expander(
                "View scan output"
            ):

                st.code(
                    result.stdout
                )

        st.rerun()

    else:

        st.error(
            "Scan failed."
        )

        if result.stdout:
            st.code(result.stdout)

        if result.stderr:
            st.code(result.stderr)


# ============================================================
# REFRESH
# ============================================================

if refresh_button:

    with st.spinner(
        f"Refreshing {keyword_text} | {location_text}..."
    ):

        result = run_main_command(
            "refresh",
            selected_keyword,
            selected_location,
        )

    if result.returncode == 0:

        st.success(
            "Latest jobs refreshed successfully."
        )

        if result.stdout:

            with st.expander(
                "📊 Refresh result"
            ):

                st.code(
                    result.stdout
                )

        st.rerun()

    else:

        st.error(
            "Refresh failed."
        )

        if result.stdout:
            st.code(result.stdout)

        if result.stderr:
            st.code(result.stderr)


# ============================================================
# HEADER
# ============================================================

st.title(
    "💼 Naukri Job Assistant"
)

st.caption(
    "Search, refresh, score and track your Naukri applications."
)

st.info(
    f"🔎 **Keyword:** {keyword_text}    "
    f"|    📍 **Location:** {location_text}"
)


# ============================================================
# LOAD JOBS
# ============================================================

jobs = load_jobs()


# ============================================================
# STATUS COUNTS
# ============================================================

status_counts = {
    "NEW": 0,
    "APPLIED": 0,
    "SKIPPED": 0,
    "FAILED": 0,
}

for job in jobs:

    status = job["status"] or "NEW"

    status_counts[status] = (
        status_counts.get(status, 0) + 1
    )


# ============================================================
# SCORE COUNTS
# ============================================================

score_90 = sum(
    1
    for job in jobs
    if (job["match_score"] or 0) >= 90
)

score_70 = sum(
    1
    for job in jobs
    if (job["match_score"] or 0) >= 70
)

score_50 = sum(
    1
    for job in jobs
    if (job["match_score"] or 0) >= 50
)


# ============================================================
# METRICS
# ============================================================

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric(
        "📋 Total Jobs",
        len(jobs),
    )

with c2:
    st.metric(
        "🔥 90+",
        score_90,
    )

with c3:
    st.metric(
        "⭐ 70+",
        score_70,
    )

with c4:
    st.metric(
        "🎯 50+",
        score_50,
    )

with c5:
    st.metric(
        "🚀 Applied",
        status_counts.get(
            "APPLIED",
            0,
        ),
    )


st.divider()


# ============================================================
# STATUS METRICS
# ============================================================

st.subheader(
    "📊 Application Status"
)

s1, s2, s3, s4 = st.columns(4)

with s1:
    st.metric(
        "🆕 New",
        status_counts.get("NEW", 0),
    )

with s2:
    st.metric(
        "🚀 Applied",
        status_counts.get("APPLIED", 0),
    )

with s3:
    st.metric(
        "⏭️ Skipped",
        status_counts.get("SKIPPED", 0),
    )

with s4:
    st.metric(
        "❌ Failed",
        status_counts.get("FAILED", 0),
    )


st.divider()


# ============================================================
# FILTER
# ============================================================

# filtered_jobs = list(jobs)


# # SCORE FILTER
# if score_filter == "90+ Score":

#     filtered_jobs = [
#         job
#         for job in filtered_jobs
#         if (job["match_score"] or 0) >= 90
#     ]

# elif score_filter == "70+ Score":

#     filtered_jobs = [
#         job
#         for job in filtered_jobs
#         if (job["match_score"] or 0) >= 70
#     ]

# elif score_filter == "50+ Score":

#     filtered_jobs = [
#         job
#         for job in filtered_jobs
#         if (job["match_score"] or 0) >= 50
#     ]


# # STATUS FILTER
# if status_filter != "All Status":

#     filtered_jobs = [
#         job
#         for job in filtered_jobs
#         if (
#             job["status"] or "NEW"
#         ) == status_filter
#     ]


# # LOCATION FILTER
# if selected_location != "All Locations":

#     location = selected_location.lower()

#     filtered_jobs = [
#         job
#         for job in filtered_jobs
#         if location in (
#             job["location"] or ""
#         ).lower()
#     ]


# ============================================================
# FILTER JOBS
# ============================================================

filtered_jobs = list(jobs)


# ============================================================
# KEYWORD RELEVANCE FILTER
# ============================================================

if selected_keyword != "All Keywords":

    filtered_jobs = [
        job
        for job in filtered_jobs
        if is_relevant_job(
            job,
            selected_keyword
        )
    ]


# ============================================================
# SCORE FILTER
# ============================================================

if score_filter == "90+ Score":

    filtered_jobs = [
        job
        for job in filtered_jobs
        if (job["match_score"] or 0) >= 90
    ]

elif score_filter == "70+ Score":

    filtered_jobs = [
        job
        for job in filtered_jobs
        if (job["match_score"] or 0) >= 70
    ]

elif score_filter == "50+ Score":

    filtered_jobs = [
        job
        for job in filtered_jobs
        if (job["match_score"] or 0) >= 50
    ]


# ============================================================
# STATUS FILTER
# ============================================================

if status_filter != "All Status":

    filtered_jobs = [
        job
        for job in filtered_jobs
        if (
            job["status"] or "NEW"
        ).upper() == status_filter
    ]


# ============================================================
# LOCATION FILTER
# ============================================================

if selected_location != "All Locations":

    selected_location_lower = (
        selected_location
        .lower()
        .strip()
    )

    filtered_jobs = [
        job
        for job in filtered_jobs
        if selected_location_lower
        in normalize_text(
            job["location"]
        )
    ]
# ============================================================
# JOB LIST
# ============================================================

st.subheader(
    "📋 Jobs"
)

st.write(
    f"Showing **{len(filtered_jobs)}** jobs"
)


if not filtered_jobs:

    st.warning(
        "No jobs match your current filters."
    )

else:

    job_db = JobDB(
        DB_PATH
    )

    status_icons = {
        "NEW": "🆕",
        "APPLIED": "🚀",
        "SKIPPED": "⏭️",
        "FAILED": "❌",
    }

    for job in filtered_jobs:

        status = (
            job["status"]
            or "NEW"
        )

        icon = status_icons.get(
            status,
            "🆕"
        )

        st.markdown("---")

        left, right = st.columns(
            [5, 1]
        )

        with left:

            st.markdown(
                f"### 💼 {job['job_title']} {icon}"
            )

            a, b = st.columns(2)

            with a:

                st.write(
                    f"🏢 **Company:** "
                    f"{job['company'] or 'Not specified'}"
                )

                st.write(
                    f"📍 **Location:** "
                    f"{job['location'] or 'Not specified'}"
                )

                st.write(
                    f"💼 **Experience:** "
                    f"{job['experience'] or 'Not specified'}"
                )

            with b:

                st.write(
                    f"⭐ **Score:** "
                    f"{job['match_score'] or 0}"
                )

                st.write(
                    f"💰 **Salary:** "
                    f"{job['salary'] or 'Not specified'}"
                )

                st.write(
                    f"📌 **Status:** {status}"
                )

            if job["skills"]:

                st.write(
                    f"🛠️ **Skills:** {job['skills']}"
                )

            if job["match_reasons"]:

                with st.expander(
                    "🎯 Match Reasons"
                ):

                    st.write(
                        job["match_reasons"]
                    )

            if job["description"]:

                with st.expander(
                    "📝 Job Description"
                ):

                    st.write(
                        job["description"]
                    )

        with right:

            st.write("")

            if job["job_url"]:

                st.link_button(
                    "🚀 Apply / Review",
                    job["job_url"],
                    use_container_width=True,
                )

            if status != "APPLIED":

                if st.button(
                    "✅ Mark Applied",
                    key=f"applied_{job['job_id']}",
                    use_container_width=True,
                ):

                    job_db.set_status(
                        job["job_id"],
                        "APPLIED",
                    )

                    st.rerun()

            if status != "SKIPPED":

                if st.button(
                    "⏭️ Skip",
                    key=f"skip_{job['job_id']}",
                    use_container_width=True,
                ):

                    job_db.set_status(
                        job["job_id"],
                        "SKIPPED",
                    )

                    st.rerun()

            if status != "FAILED":

                if st.button(
                    "❌ Failed",
                    key=f"failed_{job['job_id']}",
                    use_container_width=True,
                ):

                    job_db.set_status(
                        job["job_id"],
                        "FAILED",
                    )

                    st.rerun()

    job_db.conn.close()