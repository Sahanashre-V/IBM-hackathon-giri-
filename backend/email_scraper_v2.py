#!/usr/bin/env python3
"""
email_scraper_v2.py

Usage (CLI):
    python email_scraper_v2.py input.csv                         # IG-only scraping, writes tmp_outreach_output.csv
    python email_scraper_v2.py input.csv /path/to/chromedriver   # IG + FB (Selenium) scraping, writes tmp_outreach_output.csv

Behavior:
 - Reads input CSV (expects header row with columns like 'Name', 'IG'/'Instagram'/'IG Link', 'FB'/'Facebook'/'FB Link', and 'Email').
 - For rows missing email, tries IG scraping (requests + BeautifulSoup).
 - If chromedriver path provided, will attempt FB scraping with Selenium (interactive login required).
 - Writes output CSV named tmp_outreach_output.csv with same columns + a "Found Email" column (if original Email column missing) or overwrites Email column in the copy.
"""
import sys
import os
import csv
import time
import re
import argparse
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Only import selenium when needed to avoid forcing it on environments that don't need it
SELENIUM_AVAILABLE = False
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except Exception:
    SELENIUM_AVAILABLE = False

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

def extract_emails(text):
    if not isinstance(text, str):
        return []
    return EMAIL_RE.findall(text)

def scrape_instagram_bio(url, timeout=10):
    """Return list of emails found in IG meta description or empty list."""
    if not url or pd.isna(url):
        return []
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        bio_tag = soup.find("meta", property="og:description")
        if bio_tag and bio_tag.get("content"):
            return list(dict.fromkeys(extract_emails(bio_tag["content"])))  # preserve uniqueness
        return []
    except Exception as e:
        print(f"[IG] Error scraping {url}: {e}")
        return []

# Selenium FB helpers (only used if chromedriver path passed and selenium is available)
def init_selenium(chromedriver_path):
    if not SELENIUM_AVAILABLE:
        raise RuntimeError("Selenium is not installed. Install with: pip install selenium")
    chrome_options = Options()
    # keep visible for interactive login
    chrome_options.add_argument("--start-maximized")
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def fb_login_interactive(driver):
    print("[FB] Opening Facebook login. Please login in the opened browser window and then return here and press Enter.")
    driver.get("https://www.facebook.com/login")
    input("[FB] After logging in, press Enter in this terminal to continue...")

def scrape_facebook_about_selenium(driver, url, wait_seconds=5):
    try:
        if not url:
            return []
        if "/about" not in url:
            url = url.rstrip("/") + "/about"
        driver.get(url)
        time.sleep(wait_seconds)  # let dynamic content load
        html = driver.page_source
        emails = extract_emails(html)
        return list(dict.fromkeys(emails))
    except Exception as e:
        print(f"[FB] Error scraping {url}: {e}")
        return []

def detect_columns(df):
    """Try to auto-detect email, ig, fb columns in a DataFrame."""
    email_col = None
    for c in ["Email", "E-mail", "email", "Email Address"]:
        if c in df.columns:
            email_col = c
            break
    ig_col = None
    for c in ["IG", "Instagram", "IG Link", "ig_link", "Instagram URL", "instagram"]:
        if c in df.columns:
            ig_col = c
            break
    fb_col = None
    for c in ["FB", "Facebook", "FB Link", "facebook_link", "Facebook URL", "fb"]:
        if c in df.columns:
            fb_col = c
            break
    return email_col, ig_col, fb_col

def run_on_dataframe(df, do_fb=False, chromedriver_path=None, fb_wait_seconds=5, verbose=True):
    """
    df: pandas DataFrame (copy will be created)
    do_fb: whether to attempt FB scraping (requires chromedriver_path and selenium)
    Returns: (output_df, stats)
    """
    out = df.copy()
    email_col, ig_col, fb_col = detect_columns(df)
    if verbose:
        print(f"[INFO] Detected columns -> email: {email_col}, ig: {ig_col}, fb: {fb_col}")

    # prepare output column
    if not email_col:
        out["Found Email"] = ""

    # prepare selenium driver if needed
    driver = None
    if do_fb:
        if not chromedriver_path:
            raise ValueError("FB scraping requested but no chromedriver_path provided.")
        if not SELENIUM_AVAILABLE:
            raise RuntimeError("Selenium package not available. Install `selenium` to use FB scraping.")
        if not os.path.exists(chromedriver_path):
            raise FileNotFoundError(f"chromedriver not found at: {chromedriver_path}")
        driver = init_selenium(chromedriver_path)
        fb_login_interactive(driver)

    stats = {"rows": len(df), "found_ig": 0, "found_fb": 0, "skipped_already_have_email": 0}
    for idx, row in df.iterrows():
        cur_email = str(row.get(email_col, "")).strip() if email_col else str(row.get("Found Email", "")).strip()
        if cur_email:
            stats["skipped_already_have_email"] += 1
            continue

        found = ""
        # IG scraping first
        ig_url = row.get(ig_col, "") if ig_col else ""
        if ig_url and not pd.isna(ig_url):
            try:
                ig_emails = scrape_instagram_bio(ig_url)
                if ig_emails:
                    found = ig_emails[0]
                    stats["found_ig"] += 1
            except Exception as e:
                if verbose:
                    print(f"[IG] Row {idx+1} error: {e}")

        # FB scraping fallback if requested and nothing found
        if not found and do_fb and fb_col:
            fb_url = row.get(fb_col, "") if fb_col else ""
            if fb_url and not pd.isna(fb_url):
                try:
                    fb_emails = scrape_facebook_about_selenium(driver, fb_url, wait_seconds=fb_wait_seconds)
                    if fb_emails:
                        found = fb_emails[0]
                        stats["found_fb"] += 1
                except Exception as e:
                    if verbose:
                        print(f"[FB] Row {idx+1} error: {e}")

        # write back to output DataFrame
        if email_col:
            out.at[idx, email_col] = found
        else:
            out.at[idx, "Found Email"] = found

        if verbose:
            if found:
                print(f"[FOUND] Row {idx+1}: {found}")
            else:
                print(f"[MISS] Row {idx+1}: no email found")

    if driver:
        try:
            driver.quit()
        except Exception:
            pass

    return out, stats

def main_cli():
    parser = argparse.ArgumentParser(description="Email finder for OutreachLeads CSV.")
    parser.add_argument("input_csv", help="Path to input CSV (OutreachLeads export).")
    parser.add_argument("chromedriver", nargs="?", default=None, help="Optional path to chromedriver to enable FB scraping.")
    parser.add_argument("--fb-wait", type=int, default=5, help="Seconds to wait after FB page load for dynamic content.")
    parser.add_argument("--no-ig", action="store_true", help="Skip Instagram scraping (not recommended).")
    args = parser.parse_args()

    if not os.path.exists(args.input_csv):
        print(f"[ERROR] input CSV not found: {args.input_csv}")
        sys.exit(2)

    df = pd.read_csv(args.input_csv)
    print(f"[INFO] Read {len(df)} rows from {args.input_csv}")

    do_fb = bool(args.chromedriver)
    do_ig = not args.no_ig

    # run IG + optional FB
    out_df, stats = run_on_dataframe(df, do_fb=do_fb, chromedriver_path=args.chromedriver, fb_wait_seconds=args.fb_wait)
    print(f"[DONE] Stats: {stats}")

    out_path = "tmp_outreach_output.csv"
    out_df.to_csv(out_path, index=False)
    print(f"[INFO] Wrote results to {out_path}")

if __name__ == "__main__":
    main_cli()
