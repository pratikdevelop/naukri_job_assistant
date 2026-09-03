import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path


class JobDB:

    def __init__(self, path: Path):
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                job_title TEXT,
                company TEXT,
                location TEXT,
                experience TEXT,
                salary TEXT,
                skills TEXT,
                description TEXT,
                posted_date TEXT,
                job_url TEXT UNIQUE,
                match_score INTEGER DEFAULT 0,
                match_reasons TEXT,
                status TEXT DEFAULT 'NEW',
                first_seen TEXT,
                last_seen TEXT,
                applied_at TEXT
            )
            """
        )
        self.ensure_status_column(self.conn)

        self.conn.commit()

    @staticmethod
    def make_id(job):
        raw = (
            job.get("job_url")
            or "|".join(
                [
                    job.get("job_title", ""),
                    job.get("company", ""),
                    job.get("location", ""),
                ]
            )
        )

        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    def upsert_job(self, job):
        now = datetime.now().isoformat(timespec="seconds")
        jid = self.make_id(job)

        old = self.conn.execute(
            "SELECT job_id FROM jobs WHERE job_id=?",
            (jid,),
        ).fetchone()

        if old:
            values = (
                job.get("job_title", ""),
                job.get("company", ""),
                job.get("location", ""),
                job.get("experience", ""),
                job.get("salary", ""),
                job.get("skills", ""),
                job.get("description", ""),
                job.get("posted_date", ""),
                job.get("job_url", ""),
                job.get("match_score", 0),
                job.get("match_reasons", ""),
                now,
                jid,
            )

            self.conn.execute(
                """
                UPDATE jobs
                SET
                    job_title=?,
                    company=?,
                    location=?,
                    experience=?,
                    salary=?,
                    skills=?,
                    description=?,
                    posted_date=?,
                    job_url=?,
                    match_score=?,
                    match_reasons=?,
                    last_seen=?
                WHERE job_id=?
                """,
                values,
            )

            self.conn.commit()
            return False

        values = (
            jid,
            job.get("job_title", ""),
            job.get("company", ""),
            job.get("location", ""),
            job.get("experience", ""),
            job.get("salary", ""),
            job.get("skills", ""),
            job.get("description", ""),
            job.get("posted_date", ""),
            job.get("job_url", ""),
            job.get("match_score", 0),
            job.get("match_reasons", ""),
            "NEW",
            now,
            now,
            None,
        )

        self.conn.execute(
            """
            INSERT INTO jobs (
                job_id,
                job_title,
                company,
                location,
                experience,
                salary,
                skills,
                description,
                posted_date,
                job_url,
                match_score,
                match_reasons,
                status,
                first_seen,
                last_seen,
                applied_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            values,
        )

        self.conn.commit()
        return True

    def pending_jobs(self, min_score=50):
        return self.conn.execute(
            """
            SELECT *
            FROM jobs
            WHERE status != 'APPLIED'
              AND match_score >= ?
            ORDER BY match_score DESC, first_seen DESC
            """,
            (min_score,),
        ).fetchall()

    def set_status(self, jid, status):
        now = datetime.now().isoformat(timespec="seconds")

        self.conn.execute(
            """
            UPDATE jobs
            SET
                status=?,
                applied_at=
                    CASE
                        WHEN ?='APPLIED' THEN ?
                        ELSE applied_at
                    END
            WHERE job_id=?
            """,
            (status, status, now, jid),
        )

        self.conn.commit()

    def all_jobs(self):
        return self.conn.execute(
            """
            SELECT *
            FROM jobs
            ORDER BY match_score DESC, first_seen DESC
            """
        ).fetchall()

    def stats(self):
        total = self.conn.execute(
            "SELECT COUNT(*) FROM jobs"
        ).fetchone()[0]

        rows = self.conn.execute(
            """
            SELECT status, COUNT(*) n
            FROM jobs
            GROUP BY status
            """
        ).fetchall()

        return {
            "total": total,
            **{row["status"]: row["n"] for row in rows},
        }

    @staticmethod
    def ensure_status_column(conn):
        columns = conn.execute(
            "PRAGMA table_info(jobs)"
        ).fetchall()

        column_names = [column[1] for column in columns]

        if "status" not in column_names:
            conn.execute(
                """
                ALTER TABLE jobs
                ADD COLUMN status TEXT DEFAULT 'NEW'
                """
            )