from urllib.parse import urljoin
from selenium.webdriver.common.by import By

BASE = "https://www.naukri.com"

def text(el):
    try:
        return " ".join(el.text.split())
    except Exception:
        return ""

def first(card, selectors):
    for selector in selectors:
        try:
            value = text(card.find_element(By.CSS_SELECTOR, selector))
            if value:
                return value
        except Exception:
            pass
    return ""

def attr(card, selectors, name):
    for selector in selectors:
        try:
            value = card.find_element(By.CSS_SELECTOR, selector).get_attribute(name)
            if value:
                return value
        except Exception:
            pass
    return ""

def extract_jobs_from_page(driver):
    cards = []
    for selector in ["article.jobTuple", "div.srp-jobtuple-wrapper", "div.jobTuple", "article"]:
        try:
            cards = driver.find_elements(By.CSS_SELECTOR, selector)
            if cards:
                break
        except Exception:
            pass

    result = []
    for card in cards:
        title = first(card, ["a.title", "a[class*='title']", "h2 a", "h3 a"])
        url = attr(card, ["a.title", "a[class*='title']", "h2 a", "h3 a"], "href")
        if not title or not url:
            continue

        result.append({
            "job_title": title,
            "company": first(card, ["a.comp-name", "a[class*='comp-name']", "div[class*='company'] a"]) or "Unknown",
            "location": first(card, ["span.locWd", "span[class*='location']", "div[class*='location']"]) or "Not specified",
            "experience": first(card, ["span.expwd", "span[class*='experience']"]),
            "salary": first(card, ["span.sal", "span[class*='salary']"]),
            "skills": first(card, ["ul.tags-gt", "div[class*='tags']", "div[class*='skills']"]),
            "description": first(card, ["div.job-desc", "div[class*='job-desc']", "div[class*='description']"]),
            "posted_date": first(card, ["span.job-post-day", "span[class*='posted']"]),
            "job_url": urljoin(BASE, url)
        })
    return result
