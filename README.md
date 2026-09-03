# Naukri Job Assistant

## Features
- Chrome + Selenium
- Interactive Naukri login
- Keyword/location job search
- Duplicate tracking with SQLite
- MERN/Node/React/Full Stack match scoring
- CSV export
- Local dashboard with Apply / Review buttons
- Manual final application step and status tracking

## Install (Windows)
```powershell
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Login
```powershell
python main.py login
```
Complete login, OTP, and CAPTCHA yourself in Chrome.

## Scan
```powershell
python main.py scan
python main.py scan --keyword "MERN Developer" --location "Indore"
```

## Apply workflow
```powershell
python main.py apply --min-score 50
```
The program opens each job. Review it and click Naukri's Apply button yourself, then mark the result in the terminal.

## Other
```powershell
python main.py stats
python main.py export
python main.py dashboard
```

Files created:
- data/jobs.db
- data/jobs.csv
- data/dashboard.html
- chrome_profile/ (local browser session)

Naukri's DOM can change, so selectors are centralized in `naukri_assistant/extractor.py`.

This project does not bypass CAPTCHA/OTP/security controls, rate limits, or mass-submit applications.
