import csv

FIELDS = ["job_id","job_title","company","location","experience","salary","skills","posted_date","job_url","match_score","match_reasons","status","first_seen","last_seen","applied_at"]

def export_csv(db, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in db.all_jobs():
            writer.writerow({k: row[k] for k in FIELDS})
