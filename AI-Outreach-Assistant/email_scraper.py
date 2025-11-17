# email_scraper.py

import time
import re
import gspread
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from oauth2client.service_account import ServiceAccountCredentials

def launch_browser():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = Service("chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.instagram.com/")
    driver.execute_script("window.open('https://www.facebook.com/', '_blank');")
    return driver

def extract_emails_from_text(text):
    return list(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)))

def extract_email_from_instagram(driver, insta_url):
    try:
        driver.get(insta_url)
        time.sleep(5)
        html = driver.page_source
        return extract_emails_from_text(html)
    except Exception as e:
        print(f"    ⚠️ IG scraping error: {e}")
        return []

def extract_email_from_facebook(driver, fb_url):
    try:
        driver.get(fb_url + "/about")
        time.sleep(5)
        html = driver.page_source
        return extract_emails_from_text(html)
    except Exception as e:
        print(f"    ⚠️ FB scraping error: {e}")
        return []

def update_email_in_sheet(row_index, email, sheet):
    sheet.update_cell(row_index, 5, email)
    print(f"✅ Found & Updated: {email}")

def main():
    print("🔗 Connecting to Google Sheet...")
    OUTREACH=os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(OUTREACH, scope)
    client = gspread.authorize(creds)

    sheet = client.open("OutreachLog").worksheet("OutreachLeads")
    data = sheet.get_all_records()
    driver = launch_browser()

    print("\n👤 Login to Instagram and Facebook in the browser that opened.")
    input("🔒 Press ENTER here **after logging in**...")

    print("\n🚀 Starting email scraping...\n")
    for i, row in enumerate(data, start=2):
        existing_email = row.get("Email", "").strip()
        if existing_email:
            continue

        insta = row.get("Instagram Link", "").strip()
        fb = row.get("Facebook Link", "").strip()
        all_emails = []

        print(f"🔎 Scraping Row {i}:")
        print(f"  - IG: {insta if insta else '❌'}")
        print(f"  - FB: {fb if fb else '❌'}")

        if insta:
            all_emails += extract_email_from_instagram(driver, insta)

        if fb:
            all_emails += extract_email_from_facebook(driver, fb)

        unique_emails = list(set(all_emails))
        if unique_emails:
            update_email_in_sheet(i, unique_emails[0], sheet)
        else:
            print("❌ No email found.\n")

    driver.quit()
    print("\n🎉 Done scraping!")

if __name__ == "__main__":
    main()