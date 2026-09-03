import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

def load_config(path: Path):
    load_dotenv(path.parent / ".env")
    with open(path, encoding="utf-8") as f:
        c = yaml.safe_load(f)
    c["pages_per_keyword"] = int(os.getenv("PAGES_PER_KEYWORD", "3"))
    c["chrome_profile_dir"] = os.getenv("CHROME_PROFILE_DIR", "chrome_profile")
    c["min_delay"] = float(os.getenv("MIN_DELAY_SECONDS", "2"))
    c["max_delay"] = float(os.getenv("MAX_DELAY_SECONDS", "5"))
    return c
