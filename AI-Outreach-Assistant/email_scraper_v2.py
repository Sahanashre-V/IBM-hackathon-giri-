import re
import time
import gspread
import requests
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service  # ✅ IMPORT FIX

# ============================
# 🔧 Google Sheets Setup
# ============================

OUTREACH = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    OUTREACH, scope
)
client = gspread.authorize(creds)
sheet = client.open("OutreachLog").worksheet("OutreachLeads")

# ============================
# 📬 Email Extractor
# ============================
def extract_emails(text):
    return re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

# ============================
# 📸 Instagram Scraper
# ============================
def scrape_instagram_bio(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        bio_tag = soup.find("meta", property="og:description")
        if bio_tag:
            return list(set(extract_emails(bio_tag["content"])))
        return []
    except Exception as e:
        print(f"❌ IG scrape error for {url}: {e}")
        return []

# ============================
# 📘 Facebook Scraper (Selenium)
# ============================
def init_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # ✅ allow visible browser
    chrome_path = r"E:\IBM (Team - 7)\PROJECT\AI-Outreach-Assistant\chromedriver.exe"  # ✅ correct path

    service = Service(chrome_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def fb_login(driver):
    driver.get("https://www.facebook.com/login")
    input("📘 Login to Facebook in the opened Chrome window, then press Enter here...")

def scrape_facebook_about_selenium(driver, url):
    try:
        if "/about" not in url:
            url = url.rstrip("/") + "/about"

        driver.get(url)
        time.sleep(5)  # Wait for dynamic content to load

        html = driver.page_source
        emails = extract_emails(html)
        return list(set(emails))
    except Exception as e:
        print(f"❌ FB Selenium scrape error for {url}: {e}")
        return []

# ============================
# 🚀 Main Loop
# ============================
def main():
    rows = sheet.get_all_values()

    driver = init_selenium()
    fb_login(driver)

    for i, row in enumerate(rows[1:], start=2):  # skip header
        name = row[0].strip()
        ig_link = row[11].strip()
        fb_link = row[12].strip()
        email = row[4].strip()

        if email:
            continue  # already has email

        print(f"\n🔎 Row {i} - {name}")
        found_email = None

        # Instagram (fast)
        if ig_link:
            ig_emails = scrape_instagram_bio(ig_link)
            if ig_emails:
                found_email = ig_emails[0]

        # Facebook (Selenium)
        if not found_email and fb_link:
            fb_emails = scrape_facebook_about_selenium(driver, fb_link)
            if fb_emails:
                found_email = fb_emails[0]

        # Update sheet
        if found_email:
            sheet.update_cell(i, 5, found_email)
            print(f"✅ Email found: {found_email}")
        else:
            print("❌ No email found.")

    driver.quit()
    print("\n🎉 Done!")

if __name__ == "__main__":
    main()