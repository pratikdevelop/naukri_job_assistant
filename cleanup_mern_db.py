import sqlite3
import shutil
from pathlib import Path
from datetime import datetime


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "jobs.db"


def normalize(value):
    return str(value or "").lower().strip()


def is_mern_job(row):
    """
    Keep a job when:
    1. MERN is explicitly mentioned, OR
    2. At least 3 of the 4 MERN technologies are present:
       MongoDB, Express, React, Node.js
    """

    text = " ".join(
        [
            normalize(row["job_title"]),
            normalize(row["skills"]),
            normalize(row["description"]),
        ]
    )

    # Direct MERN mention
    if "mern" in text:
        return True

    technologies = {
        "mongodb": [
            "mongodb",
            "mongo db",
            "mongo",
        ],
        "express": [
            "express.js",
            "express js",
            "express",
        ],
        "react": [
            "react.js",
            "react js",
            "reactjs",
        ],
        "node": [
            "node.js",
            "node js",
            "nodejs",
        ],
    }

    matches = 0

    for variants in technologies.values():

        if any(
            variant in text
            for variant in variants
        ):
            matches += 1

    return matches >= 3


def main():

    if not DB_PATH.exists():

        print(
            f"Database not found: {DB_PATH}"
        )
        return

    # ---------------------------------------------------------
    # BACKUP
    # ---------------------------------------------------------

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        ROOT
        / "data"
        / f"jobs_backup_{timestamp}.db"
    )

    shutil.copy2(
        DB_PATH,
        backup_path
    )

    print(
        f"Backup created:\n{backup_path}"
    )

    # ---------------------------------------------------------
    # OPEN DB
    # ---------------------------------------------------------

    conn = sqlite3.connect(
        str(DB_PATH)
    )

    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT
            job_id,
            job_title,
            company,
            location,
            skills,
            description
        FROM jobs
        """
    ).fetchall()

    total = len(rows)

    # ---------------------------------------------------------
    # FIND NON-MERN JOBS
    # ---------------------------------------------------------

    delete_ids = []

    keep_count = 0

    for row in rows:

        if is_mern_job(row):

            keep_count += 1

        else:

            delete_ids.append(
                row["job_id"]
            )

    # ---------------------------------------------------------
    # CONFIRM
    # ---------------------------------------------------------

    print()
    print("=" * 60)
    print("MERN DATABASE CLEANUP")
    print("=" * 60)

    print(
        f"Total jobs:       {total}"
    )

    print(
        f"MERN jobs kept:    {keep_count}"
    )

    print(
        f"Other jobs removed: {len(delete_ids)}"
    )

    print("=" * 60)

    if not delete_ids:

        print(
            "\nNothing to remove."
        )

        conn.close()
        return

    # ---------------------------------------------------------
    # DELETE NON-MERN
    # ---------------------------------------------------------

    conn.executemany(
        """
        DELETE FROM jobs
        WHERE job_id = ?
        """,
        [
            (job_id,)
            for job_id in delete_ids
        ]
    )

    conn.commit()

    # ---------------------------------------------------------
    # VERIFY
    # ---------------------------------------------------------

    remaining = conn.execute(
        "SELECT COUNT(*) FROM jobs"
    ).fetchone()[0]

    print()
    print(
        f"Database now contains: {remaining} jobs"
    )

    print(
        f"Backup available at: {backup_path}"
    )

    conn.close()


if __name__ == "__main__":
    main()