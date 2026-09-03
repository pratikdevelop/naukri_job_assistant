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

def main():
    p = argparse.ArgumentParser(description="Naukri semi-automated job assistant")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("login")
    s = sub.add_parser("scan")
    s.add_argument("--keyword")
    s.add_argument("--location")
    a = sub.add_parser("apply")
    a.add_argument("--min-score", type=int, default=50)
    sub.add_parser("stats")
    sub.add_parser("export")
    sub.add_parser("dashboard")
    args = p.parse_args()

    cfg = load_config(ROOT / "config.yaml")
    db = JobDB(DATA / "jobs.db")

    if args.cmd == "login":
        b = NaukriBrowser(cfg)
        try:
            b.login_interactive()
        finally:
            b.close()

    elif args.cmd == "scan":
        b = NaukriBrowser(cfg)
        try:
            kws = [args.keyword] if args.keyword else cfg["keywords"]["primary"] + cfg["keywords"]["secondary"]
            locs = [args.location] if args.location else cfg["locations"]
            new = 0
            for kw in kws:
                for loc in locs:
                    print(f"Searching: {kw} | {loc}")
                    jobs = b.search_jobs(kw, loc, cfg["experience"]["min"], cfg["experience"]["max"], cfg["pages_per_keyword"])
                    for job in jobs:
                        job["match_score"], job["match_reasons"] = score_job(job, cfg)
                        new += db.upsert_job(job)
            export_csv(db, DATA / "jobs.csv")
            write_dashboard(db, DATA / "dashboard.html")
            print(f"Processed {new} new jobs.")
        finally:
            b.close()

    elif args.cmd == "apply":
        jobs = db.pending_jobs(args.min_score)
        if not jobs:
            print("No pending jobs match that score.")
            return
        b = NaukriBrowser(cfg)
        try:
            for i, row in enumerate(jobs, 1):
                j = dict(row)
                print("\n" + "=" * 70)
                print(f"[{i}/{len(jobs)}] {j['job_title']} @ {j['company']}")
                print(f"Score: {j['match_score']} | {j['location']}")
                print(f"Why: {j['match_reasons']}")
                print(j["job_url"])
                b.open_job(j["job_url"])
                while True:
                    x = input("[a]pplied [s]kipped [f]ailed [q]uit: ").strip().lower()
                    if x in {"a","s","f","q"}:
                        break
                if x == "q":
                    break
                db.set_status(j["job_id"], {"a":"APPLIED","s":"SKIPPED","f":"FAILED"}[x])
        finally:
            b.close()
        export_csv(db, DATA / "jobs.csv")
        write_dashboard(db, DATA / "dashboard.html")

    elif args.cmd == "stats":
        print(db.stats())

    elif args.cmd == "export":
        export_csv(db, DATA / "jobs.csv")
        print(DATA / "jobs.csv")

    elif args.cmd == "dashboard":
        write_dashboard(db, DATA / "dashboard.html")
        print(DATA / "dashboard.html")

if __name__ == "__main__":
    main()
