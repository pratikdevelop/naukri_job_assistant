from html import escape

def write_dashboard(db, path):
    cards = []
    for row in db.all_jobs():
        title = escape(row["job_title"] or "")
        company = escape(row["company"] or "")
        location = escape(row["location"] or "")
        reason = escape(row["match_reasons"] or "")
        url = escape(row["job_url"] or "", quote=True)
        status = escape(row["status"] or "")
        cards.append(f'<div class="card"><b>{row["match_score"]}/100</b><h2>{title}</h2><p>{company} · {location}</p><p>{reason}</p><p>Status: <b>{status}</b></p><a href="{url}" target="_blank">Apply / Review</a></div>')
    html = '<!doctype html><html><head><meta charset="utf-8"><title>Naukri Dashboard</title><style>body{font-family:Arial;max-width:1000px;margin:30px auto}.card{border:1px solid #ddd;border-radius:12px;padding:18px;margin:12px}.card>a{display:inline-block;padding:10px;border:1px solid #333;border-radius:8px;text-decoration:none}</style></head><body><h1>Naukri Job Dashboard</h1>' + ''.join(cards) + '</body></html>'
    path.write_text(html, encoding="utf-8")
