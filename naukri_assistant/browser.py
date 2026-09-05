from pathlib import Path
from time import sleep
from urllib.parse import quote_plus
import random

from selenium import webdriver
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
)

from .extractor import extract_jobs_from_page


class NaukriBrowser:
    """
    Selenium browser wrapper for Naukri.

    Features:
    - Persistent Chrome profile
    - Automatic Chrome restart
    - Retry failed pages
    - Handles Selenium and lower-level connection errors
    - Continues to the next page/search when a page fails
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.min_delay = cfg.get("min_delay", 2)
        self.max_delay = cfg.get("max_delay", 5)
        self.driver = None

        self.start_driver()

    # ==========================================================
    # START CHROME
    # ==========================================================

    def start_driver(self, retries=3):
        """
        Start ChromeDriver with the persistent Naukri profile.
        Retries startup if Chrome crashes.
        """

        last_error = None

        for attempt in range(1, retries + 1):

            try:
                print(
                    f"Starting Chrome "
                    f"(attempt {attempt}/{retries})..."
                )

                options = webdriver.ChromeOptions()

                profile = Path(
                    self.cfg["chrome_profile_dir"]
                ).resolve()

                profile.mkdir(
                    parents=True,
                    exist_ok=True
                )

                options.add_argument(
                    f"--user-data-dir={profile}"
                )

                options.add_argument(
                    "--start-maximized"
                )

                options.add_argument(
                    "--disable-notifications"
                )

                options.add_argument(
                    "--remote-debugging-port=0"
                )

                options.add_argument(
                    "--disable-dev-shm-usage"
                )

                options.add_argument(
                    "--no-first-run"
                )

                options.add_argument(
                    "--no-default-browser-check"
                )

                # More stable Chrome startup
                options.add_argument(
                    "--disable-background-networking"
                )

                options.add_argument(
                    "--disable-popup-blocking"
                )

                options.add_argument(
                    "--disable-extensions"
                )

                driver = webdriver.Chrome(
                    options=options
                )

                # Avoid hanging forever on page loads.
                driver.set_page_load_timeout(45)

                driver.implicitly_wait(5)

                self.driver = driver

                print(
                    "ChromeDriver started successfully."
                )

                return

            except Exception as exc:

                last_error = exc

                print(
                    f"Chrome startup failed: {exc}"
                )

                self.driver = None

                if attempt < retries:

                    sleep(
                        2 * attempt
                    )

        raise RuntimeError(
            "Could not start Chrome after "
            f"{retries} attempts: {last_error}"
        )

    # ==========================================================
    # RESTART CHROME
    # ==========================================================

    def restart_driver(self):
        """
        Safely restart Chrome after a dead Selenium session.
        """

        print(
            "Restarting ChromeDriver..."
        )

        self.close()

        sleep(2)

        self.start_driver()

        print(
            "ChromeDriver restarted successfully."
        )

    # ==========================================================
    # CLOSE
    # ==========================================================

    def close(self):
        """
        Safely close Chrome.
        """

        if not self.driver:
            return

        try:
            self.driver.quit()

        except Exception:
            # Chrome may already be dead.
            pass

        finally:
            self.driver = None

    # ==========================================================
    # LOGIN
    # ==========================================================

    def login_interactive(self):
        """
        Open Naukri login page.

        OTP/CAPTCHA are completed manually.
        """

        if not self.driver:
            self.start_driver()

        self.driver.get(
            "https://www.naukri.com/nlogin/login"
        )

        print()
        print(
            "Complete Naukri login, OTP, "
            "and CAPTCHA manually in Chrome."
        )

        input(
            "After login is complete, "
            "press Enter here..."
        )

    # ==========================================================
    # OPEN JOB
    # ==========================================================

    def open_job(self, url):
        """
        Open a job URL.
        """

        if not self.driver:
            self.start_driver()

        try:

            self.driver.get(url)

            sleep(2)

        except Exception as exc:

            print(
                f"Could not open job: {exc}"
            )

            try:
                self.restart_driver()

                self.driver.get(url)

                sleep(2)

            except Exception as retry_error:

                print(
                    f"Retry failed: {retry_error}"
                )

    # ==========================================================
    # SEARCH JOBS
    # ==========================================================

    def search_jobs(
        self,
        keyword,
        location,
        emin,
        emax,
        pages=3
    ):
        """
        Search Naukri for a keyword/location.

        The scanner:
        - retries a failed page
        - restarts Chrome when required
        - continues to the next page if retry fails
        - removes duplicate job URLs
        """

        out = []

        slug = (
            quote_plus(keyword)
            .lower()
            .replace("+", "-")
        )

        for page in range(
            1,
            pages + 1
        ):

            url = (
                "https://www.naukri.com/"
                f"{slug}-jobs?"
                f"k={quote_plus(keyword)}"
                f"&l={quote_plus(location)}"
                f"&experience={emin}"
            )

            if page > 1:
                url += f"&page={page}"

            page_success = False

            # --------------------------------------------------
            # Retry the current page
            # --------------------------------------------------

            for attempt in range(1, 3):

                try:

                    print(
                        f"Searching page {page}: "
                        f"{keyword} | {location}"
                    )

                    if not self.driver:

                        self.start_driver()

                    self.driver.get(
                        url
                    )

                    sleep(
                        random.uniform(
                            self.min_delay,
                            self.max_delay
                        )
                    )

                    jobs = extract_jobs_from_page(
                        self.driver
                    )

                    out.extend(
                        jobs
                    )

                    page_success = True

                    break

                except TimeoutException as exc:

                    print(
                        f"Page {page} timed out "
                        f"(attempt {attempt}): {exc}"
                    )

                except WebDriverException as exc:

                    print(
                        f"Browser error on page "
                        f"{page} "
                        f"(attempt {attempt}): "
                        f"{exc}"
                    )

                except Exception as exc:

                    # Important:
                    # ConnectionResetError and some
                    # urllib3 errors can arrive here
                    # instead of WebDriverException.

                    print(
                        f"Unexpected error on page "
                        f"{page} "
                        f"(attempt {attempt}): "
                        f"{type(exc).__name__}: {exc}"
                    )

                # --------------------------------------------------
                # Restart before retry
                # --------------------------------------------------

                if attempt == 1:

                    print(
                        "Restarting browser before retry..."
                    )

                    try:
                        self.restart_driver()

                    except Exception as restart_error:

                        print(
                            "Browser restart failed: "
                            f"{restart_error}"
                        )

                    sleep(2)

            # --------------------------------------------------
            # Page failed after retries
            # --------------------------------------------------

            if not page_success:

                print(
                    f"Page {page} could not be processed."
                )

                print(
                    "Continuing with the next page..."
                )

                continue

        # ======================================================
        # REMOVE DUPLICATES
        # ======================================================

        seen = set()

        unique = []

        for job in out:

            job_url = (
                job.get("job_url")
                or ""
            ).strip()

            # If URL is missing, keep the job based
            # on title/company/location.
            if not job_url:

                job_key = "|".join(
                    [
                        job.get(
                            "job_title",
                            ""
                        ),
                        job.get(
                            "company",
                            ""
                        ),
                        job.get(
                            "location",
                            ""
                        ),
                    ]
                )

            else:
                job_key = job_url

            if job_key in seen:
                continue

            seen.add(
                job_key
            )

            unique.append(
                job
            )

        return unique