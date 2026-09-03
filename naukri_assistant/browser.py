from pathlib import Path
from time import sleep
from urllib.parse import quote_plus
import random

from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from .extractor import extract_jobs_from_page


class NaukriBrowser:

    def __init__(self, cfg):
        self.cfg = cfg

        self.min_delay = cfg["min_delay"]
        self.max_delay = cfg["max_delay"]

        self.start_driver()

    def start_driver(self):
        """Create a new ChromeDriver session."""

        options = webdriver.ChromeOptions()

        profile = Path(self.cfg["chrome_profile_dir"]).resolve()
        profile.mkdir(parents=True, exist_ok=True)

        options.add_argument(f"--user-data-dir={profile}")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")

        self.driver = webdriver.Chrome(options=options)

    def restart_driver(self):
        """Close the dead browser session and create a new one."""

        print("Restarting ChromeDriver...")

        try:
            self.driver.quit()
        except Exception:
            pass

        sleep(2)

        self.start_driver()

        print("ChromeDriver restarted successfully.")

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    def login_interactive(self):
        self.driver.get(
            "https://www.naukri.com/nlogin/login"
        )

        print(
            "Complete Naukri login, OTP, and CAPTCHA manually in Chrome."
        )

        input("After login is complete, press Enter here...")

    def open_job(self, url):
        self.driver.get(url)
        sleep(2)

    def search_jobs(
        self,
        keyword,
        location,
        emin,
        emax,
        pages=3
    ):
        out = []

        slug = quote_plus(keyword).lower().replace("+", "-")

        for page in range(1, pages + 1):

            url = (
                f"https://www.naukri.com/"
                f"{slug}-jobs?"
                f"k={quote_plus(keyword)}"
                f"&l={quote_plus(location)}"
                f"&experience={emin}"
            )

            if page > 1:
                url += f"&page={page}"

            for attempt in range(2):

                try:
                    print(
                        f"Searching page {page}: "
                        f"{keyword} | {location}"
                    )

                    self.driver.get(url)

                    sleep(
                        random.uniform(
                            self.min_delay,
                            self.max_delay
                        )
                    )

                    jobs = extract_jobs_from_page(
                        self.driver
                    )

                    out.extend(jobs)

                    break

                except WebDriverException as e:

                    print(
                        f"Browser error on page {page}: {e}"
                    )

                    if attempt == 0:

                        print(
                            "Trying to restart the browser..."
                        )

                        self.restart_driver()

                        sleep(2)

                    else:

                        print(
                            "Retry failed. "
                            "Moving to the next search."
                        )

                        break

        seen = set()
        unique = []

        for job in out:

            if job["job_url"] not in seen:

                seen.add(job["job_url"])
                unique.append(job)

        return unique