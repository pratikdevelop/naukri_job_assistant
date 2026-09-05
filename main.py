import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

import argparse
from pathlib import Path

from naukri_assistant.browser import NaukriBrowser
from naukri_assistant.config import load_config
from naukri_assistant.database import JobDB
from naukri_assistant.dashboard import write_dashboard
from naukri_assistant.exporter import export_csv
from naukri_assistant.scorer import score_job



ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

DATA.mkdir(exist_ok=True)


def get_keywords(cfg, keyword=None):
    if keyword:
        return [keyword]

    return (
        cfg["keywords"]["primary"]
        + cfg["keywords"]["secondary"]
    )


def get_locations(cfg, location=None):
    if location:
        return [location]

    return cfg["locations"]


def refresh_jobs(keyword=None, location=None):
    """
    Search Naukri and save jobs into SQLite.

    If keyword/location are provided, only that search is performed.
    Otherwise all configured keywords and locations are searched.
    """

    cfg = load_config(ROOT / "config.yaml")

    db = JobDB(DATA / "jobs.db")
    browser = NaukriBrowser(cfg)

    total_found = 0
    new_jobs = 0
    updated_jobs = 0

    try:
        keywords = get_keywords(cfg, keyword)
        locations = get_locations(cfg, location)

        print("\n🔄 Naukri Job Refresh")
        print("=" * 70)

        for kw in keywords:
            for loc in locations:

                print(f"\n🔎 Searching: {kw} | {loc}")

                jobs = browser.search_jobs(
                    kw,
                    loc,
                    cfg["experience"]["min"],
                    cfg["experience"]["max"],
                    cfg["pages_per_keyword"],
                )

                total_found += len(jobs)

                print(f"   Found: {len(jobs)} jobs")

                for job in jobs:

                    job["match_score"], job["match_reasons"] = score_job(
                        job,
                        cfg
                    )

                    inserted = db.upsert_job(job)

                    if inserted:
                        new_jobs += 1
                    else:
                        updated_jobs += 1

        # Update CSV and HTML dashboard
        export_csv(
            db,
            DATA / "jobs.csv"
        )

        write_dashboard(
            db,
            DATA / "dashboard.html"
        )

        print("\n" + "=" * 70)
        print("✅ Refresh completed")
        print(f"Jobs found:   {total_found}")
        print(f"New jobs:     {new_jobs}")
        print(f"Updated jobs: {updated_jobs}")
        print("=" * 70)

        return {
            "total_found": total_found,
            "new_jobs": new_jobs,
            "updated_jobs": updated_jobs,
        }

    finally:
        browser.close()
        db.conn.close()


def main():

    parser = argparse.ArgumentParser(
        description="Naukri semi-automated job assistant"
    )

    sub = parser.add_subparsers(
        dest="cmd",
        required=True
    )

    # LOGIN
    sub.add_parser("login")

    # SCAN
    scan = sub.add_parser("scan")

    scan.add_argument(
        "--keyword",
        help="Job keyword"
    )

    scan.add_argument(
        "--location",
        help="Job location"
    )

    # REFRESH
    refresh = sub.add_parser("refresh")

    refresh.add_argument(
        "--keyword",
        help="Job keyword"
    )

    refresh.add_argument(
        "--location",
        help="Job location"
    )

    # APPLY
    apply_parser = sub.add_parser("apply")

    apply_parser.add_argument(
        "--min-score",
        type=int,
        default=50
    )

    # OTHER COMMANDS
    sub.add_parser("stats")
    sub.add_parser("export")
    sub.add_parser("dashboard")

    args = parser.parse_args()

    cfg = load_config(
        ROOT / "config.yaml"
    )

    db = JobDB(
        DATA / "jobs.db"
    )

    # --------------------------------------------------
    # LOGIN
    # --------------------------------------------------

    if args.cmd == "login":

        browser = NaukriBrowser(cfg)

        try:
            browser.login_interactive()

        finally:
            browser.close()

    # --------------------------------------------------
    # SCAN
    # --------------------------------------------------

    elif args.cmd == "scan":

        browser = NaukriBrowser(cfg)

        try:

            keywords = get_keywords(
                cfg,
                args.keyword
            )

            locations = get_locations(
                cfg,
                args.location
            )

            new_jobs = 0

            for kw in keywords:

                for loc in locations:

                    print(
                        f"Searching: {kw} | {loc}"
                    )

                    jobs = browser.search_jobs(
                        kw,
                        loc,
                        cfg["experience"]["min"],
                        cfg["experience"]["max"],
                        cfg["pages_per_keyword"]
                    )

                    for job in jobs:

                        (
                            job["match_score"],
                            job["match_reasons"]
                        ) = score_job(
                            job,
                            cfg
                        )

                        new_jobs += db.upsert_job(
                            job
                        )

            export_csv(
                db,
                DATA / "jobs.csv"
            )

            write_dashboard(
                db,
                DATA / "dashboard.html"
            )

            print(
                f"Processed {new_jobs} new jobs."
            )

        finally:

            browser.close()

    # --------------------------------------------------
    # REFRESH
    # --------------------------------------------------

    elif args.cmd == "refresh":

        refresh_jobs(
            keyword=args.keyword,
            location=args.location
        )

    # --------------------------------------------------
    # APPLY
    # --------------------------------------------------

    elif args.cmd == "apply":

        jobs = db.pending_jobs(
            args.min_score
        )

        if not jobs:

            print(
                "No pending jobs match that score."
            )

            db.conn.close()
            return

        browser = NaukriBrowser(cfg)

        try:

            for i, row in enumerate(
                jobs,
                1
            ):

                job = dict(row)

                print(
                    "\n" + "=" * 70
                )

                print(
                    f"[{i}/{len(jobs)}] "
                    f"{job['job_title']} "
                    f"@ {job['company']}"
                )

                print(
                    f"Score: {job['match_score']} "
                    f"| {job['location']}"
                )

                print(
                    f"Why: {job['match_reasons']}"
                )

                print(
                    job["job_url"]
                )

                browser.open_job(
                    job["job_url"]
                )

                while True:

                    choice = input(
                        "[a]pplied "
                        "[s]kipped "
                        "[f]ailed "
                        "[q]uit: "
                    ).strip().lower()

                    if choice in {
                        "a",
                        "s",
                        "f",
                        "q"
                    }:
                        break

                if choice == "q":
                    break

                status_map = {
                    "a": "APPLIED",
                    "s": "SKIPPED",
                    "f": "FAILED"
                }

                db.set_status(
                    job["job_id"],
                    status_map[choice]
                )

        finally:

            browser.close()

        export_csv(
            db,
            DATA / "jobs.csv"
        )

        write_dashboard(
            db,
            DATA / "dashboard.html"
        )

    # --------------------------------------------------
    # STATS
    # --------------------------------------------------

    elif args.cmd == "stats":

        print(
            db.stats()
        )

    # --------------------------------------------------
    # EXPORT
    # --------------------------------------------------

    elif args.cmd == "export":

        export_csv(
            db,
            DATA / "jobs.csv"
        )

        print(
            DATA / "jobs.csv"
        )

    # --------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------

    elif args.cmd == "dashboard":

        write_dashboard(
            db,
            DATA / "dashboard.html"
        )

        print(
            DATA / "dashboard.html"
        )

    db.conn.close()


if __name__ == "__main__":
    main()