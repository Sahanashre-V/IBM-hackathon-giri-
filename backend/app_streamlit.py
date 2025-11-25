# app_streamlit.py
import streamlit as st
import importlib
import inspect
import pandas as pd
import io
import os
import re
import subprocess
import requests
from bs4 import BeautifulSoup
from datetime import datetime

st.set_page_config(page_title="PEC + Email Finder — Streamlit UI", layout="wide")
st.title("PEC Bulk Generator & Email Finder — Streamlit UI")

st.markdown(
    """
    Use the tabs to:
    - Generate PEC messages (CSV or Google Sheets)
    - Find missing emails using Instagram scraping (and optionally run the local Selenium FB script)
    
    **Important security notes**
    - Do not upload your service-account JSON publicly.
    - Running Selenium (Facebook) requires a local chromedriver and manual login; this should be done only on your local machine.
    """
)

# Attempt to import the PEC generator module (assumes app_streamlit.py is in same folder as bulk_pec_generator.py)
MOD_NAME = "bulk_pec_generator"
module = None
try:
    module = importlib.import_module(MOD_NAME)
    st.success(f"Imported module `{MOD_NAME}` from: {getattr(module, '__file__', 'unknown')}")
except Exception as e:
    st.warning(f"Could not import `{MOD_NAME}` automatically. Make sure `bulk_pec_generator.py` is in the same folder. Error: {e}")

# Attempt to detect presence of the selenium fb script (the user pasted it)
SELENIUM_SCRIPT_NAME = "fb_email_scraper.py"  # change if your file is named differently
selenium_script_present = os.path.exists(SELENIUM_SCRIPT_NAME)

if not selenium_script_present:
    st.info(f"Selenium FB script `{SELENIUM_SCRIPT_NAME}` not found in project root. To enable FB scraping, place your script in the same folder and name it `{SELENIUM_SCRIPT_NAME}` (or edit this file).")

# ------------------------------------------------------------
# Helper functions for email extraction (same logic as your script)
# ------------------------------------------------------------
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

def extract_emails(text):
    if not isinstance(text, str):
        return []
    return EMAIL_RE.findall(text)

def scrape_instagram_bio(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        bio_tag = soup.find("meta", property="og:description")
        if bio_tag and bio_tag.get("content"):
            return list(set(extract_emails(bio_tag["content"])))
        return []
    except Exception as e:
        st.warning(f"IG scrape error for {url}: {e}")
        return []

# ------------------------------------------------------------
# UI: Tabs
# ------------------------------------------------------------
tabs = st.tabs(["PEC Generator", "Email Finder", "About / Run Notes"])

# -------------------------
# TAB 1: PEC Generator (CSV or Google Sheets) - mostly same as before
# -------------------------
with tabs[0]:
    st.header("PEC Generator")
    st.markdown("Generate PEC messages from your OutreachLeads sheet (CSV or Google Sheets).")

    mode = st.radio("Mode", ["CSV (safe, recommended)", "Google Sheets (requires credentials)"], key="pec_mode")

    st.subheader("Identity settings (overrides module constants during preview/run)")
    your_name = st.text_input("Your name", value=getattr(module, "YOUR_NAME", "Girinath") if module else "Girinath")
    your_city = st.text_input("Your city", value=getattr(module, "YOUR_CITY", "Chennai") if module else "Chennai")
    your_brand = st.text_input("Your brand", value=getattr(module, "YOUR_BRAND", "BlakShyft") if module else "BlakShyft")
    your_portfolio = st.text_input("Your portfolio URL", value=getattr(module, "YOUR_PORTFOLIO", "https://yourportfolio.com") if module else "https://yourportfolio.com")

    def generate_from_df(df, templates_dict, config):
        out_rows = []
        for idx, row in df.iterrows():
            status = str(row.get("Status", "")).strip().lower()
            if status in ["sent", "replied"]:
                continue
            tag = str(row.get("Tag", "")).strip()
            if not tag or tag not in templates_dict:
                out_rows.append({
                    "Name": row.get("Name", ""),
                    "Generated PEC": f"❌ Skipped (unknown/empty tag: '{tag}')"
                })
                continue
            data = {
                "artist_name": row.get("Name", ""),
                "your_name": config["your_name"],
                "city": config["city"],
                "brand": config["brand"],
                "portfolio": config["portfolio"],
                "event": row.get("Event", ""),
                "venue": row.get("Venue", ""),
                "date": row.get("Date", "")
            }
            try:
                msg = templates_dict[tag].format(**data)
            except Exception as e:
                msg = f"❌ Template format error: {e}"
            out_rows.append({"Name": row.get("Name", ""), "Generated PEC": msg})
        out_df = pd.DataFrame(out_rows)
        return out_df

    if mode.startswith("CSV"):
        uploaded = st.file_uploader("Upload OutreachLeads CSV", type=["csv"], accept_multiple_files=False, key="pec_csv")
        if uploaded:
            df = pd.read_csv(uploaded)
            st.write("Preview of uploaded sheet (first 10 rows):")
            st.dataframe(df.head(10))
            templates_dict = getattr(module, "templates", {}) if module else {}
            config = {"your_name": your_name, "city": your_city, "brand": your_brand, "portfolio": your_portfolio}
            out_df = generate_from_df(df, templates_dict, config)
            st.markdown("### Generated PECs (preview)")
            st.dataframe(out_df.head(50))
            csv_bytes = out_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download GeneratedPECs.csv", data=csv_bytes, file_name="GeneratedPECs.csv", mime="text/csv")

    else:
        st.info("Google Sheets mode will connect to the sheet named `OutreachLog`. Upload the service-account JSON and authorize.")
        uploaded_key = st.file_uploader("Upload service-account JSON (keep private)", type=["json"], key="pec_servicekey")
        sheet_name = st.text_input("Google Spreadsheet name (default: OutreachLog)", value="OutreachLog", key="pec_sheetname")
        leads_ws_name = st.text_input("Leads worksheet name (default: OutreachLeads)", value="OutreachLeads", key="pec_leadsname")
        output_ws_name = st.text_input("Output worksheet name (default: GeneratedPECs)", value="GeneratedPECs", key="pec_outputname")
        operate = st.checkbox("Allow writing to Google Sheets (will update Status + Timestamp and add output sheet)", value=False, key="pec_operate")
        run_button = st.button("Preview generation from Google Sheet", key="pec_run")

        if run_button:
            if not uploaded_key:
                st.error("Please upload the service-account JSON file.")
            else:
                # save key to temp path
                key_path = os.path.join(".", uploaded_key.name)
                with open(key_path, "wb") as f:
                    f.write(uploaded_key.getbuffer())
                try:
                    import gspread
                    from oauth2client.service_account import ServiceAccountCredentials
                except Exception as e:
                    st.error("Missing libraries: please `pip install gspread oauth2client`. Error: " + str(e))
                    st.stop()
                scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                creds = ServiceAccountCredentials.from_json_keyfile_name(key_path, scope)
                client = gspread.authorize(creds)
                try:
                    sh = client.open(sheet_name)
                    leads_ws = sh.worksheet(leads_ws_name)
                except Exception as e:
                    st.error(f"Failed to open sheet/worksheet: {e}")
                    st.stop()
                rows = leads_ws.get_all_values()
                if not rows or len(rows) < 2:
                    st.error("No data (or only header) found in worksheet.")
                else:
                    headers = rows[0]
                    data_rows = rows[1:]
                    df = pd.DataFrame(data_rows, columns=headers)
                    st.write("Preview of sheet (first 10 rows):")
                    st.dataframe(df.head(10))
                    templates_dict = getattr(module, "templates", {})
                    config = {"your_name": your_name, "city": your_city, "brand": your_brand, "portfolio": your_portfolio}
                    out_df = generate_from_df(df, templates_dict, config)
                    st.markdown("### Generated PECs (preview)")
                    st.dataframe(out_df.head(50))
                    if operate:
                        if st.button("Write GeneratedPECs sheet + update statuses (Confirm)", key="pec_write"):
                            # create/clear output worksheet then append
                            try:
                                try:
                                    output_ws = sh.worksheet(output_ws_name)
                                    output_ws.clear()
                                except Exception:
                                    output_ws = sh.add_worksheet(title=output_ws_name, rows="100", cols="3")
                                output_ws.append_row(["Name", "Generated PEC"])
                                for _, r in out_df.iterrows():
                                    output_ws.append_row([r["Name"], r["Generated PEC"]])
                                st.success(f"Output written to worksheet '{output_ws_name}'")
                            except Exception as e:
                                st.error(f"Failed to write output sheet: {e}")

                            # update statuses
                            try:
                                col_map = {key: headers.index(key) for key in headers}
                                for idx0, row in df.iterrows():
                                    status = str(row.get("Status", "")).strip().lower()
                                    if status in ["sent", "replied"]:
                                        continue
                                    tag = str(row.get("Tag", "")).strip()
                                    if not tag or tag not in templates_dict:
                                        continue
                                    sheet_row = idx0 + 2
                                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    leads_ws.update_cell(sheet_row, col_map["Status"] + 1, "Sent")
                                    leads_ws.update_cell(sheet_row, col_map["Timestamp"] + 1, timestamp)
                                st.success("Statuses/timestamps attempted to be updated.")
                            except Exception as e:
                                st.error(f"Failed to update status/timestamp: {e}")
                # cleanup temp key
                try:
                    if os.path.exists(key_path):
                        os.remove(key_path)
                except Exception:
                    pass

# -------------------------
# TAB 2: Email Finder
# -------------------------
with tabs[1]:
    st.header("Email Finder")
    st.markdown(
        """
        This runs Instagram bio scraping (server-side) to discover emails. Facebook scraping uses Selenium and must be run locally:
        - IG scraping: runs inside Streamlit, safe to use here.
        - FB scraping (Selenium): invoked as a local subprocess (requires chromedriver and interactive login). Use only if you understand the security and interactive requirements.
        """
    )
    email_mode = st.radio("Mode", ["CSV (upload)", "Google Sheets (connect)"], key="email_mode")

    run_ig = st.button("Run IG email scrape (only)", key="run_ig")
    run_fb = st.button("Run FB email scrape (Selenium, local only)", key="run_fb")

    if email_mode.startswith("CSV"):
        uploaded = st.file_uploader("Upload OutreachLeads CSV", type=["csv"], accept_multiple_files=False, key="email_csv")
        if uploaded:
            df = pd.read_csv(uploaded)
            st.write("Preview (first 10 rows):")
            st.dataframe(df.head(10))
            # ensure columns exist
            if "Name" not in df.columns or ("Email" not in df.columns and "E-mail" not in df.columns and "Email Address" not in df.columns):
                st.info("Your CSV should ideally contain a column named 'Email' and 'Name'. The app will still attempt to use column index positions.")
            # Normalize: choose email column if present
            email_col = None
            for c in ["Email", "E-mail", "email", "Email Address"]:
                if c in df.columns:
                    email_col = c
                    break

            ig_col = None
            for c in ["IG", "Instagram", "IG Link", "ig_link", "Instagram URL"]:
                if c in df.columns:
                    ig_col = c
                    break

            fb_col = None
            for c in ["FB", "Facebook", "FB Link", "facebook_link", "FB Link"]:
                if c in df.columns:
                    fb_col = c
                    break

            st.write("Columns detected:", {"email_col": email_col, "ig_col": ig_col, "fb_col": fb_col})

            # Run IG scraping
            if run_ig:
                st.info("Running IG scraping for rows missing email...")
                results = []
                for idx, row in df.iterrows():
                    cur_email = str(row.get(email_col, "")).strip() if email_col else ""
                    if cur_email:
                        results.append(cur_email)
                        continue
                    ig_url = row.get(ig_col, "") if ig_col else ""
                    if not ig_url or pd.isna(ig_url):
                        results.append("")
                        continue
                    try:
                        found = scrape_instagram_bio(ig_url)
                        results.append(found[0] if found else "")
                    except Exception as e:
                        results.append("")
                        st.warning(f"Row {idx+1}: IG scrape error: {e}")
                df_result = df.copy()
                if email_col:
                    df_result[email_col] = results
                else:
                    df_result["Found Email"] = results
                st.markdown("### Results (first 50 rows)")
                st.dataframe(df_result.head(50))
                csv_bytes = df_result.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV with found emails", data=csv_bytes, file_name="Outreach_with_emails.csv", mime="text/csv")

            # Run FB (Selenium) as subprocess (optional)
            if run_fb:
                if not selenium_script_present:
                    st.error(f"Selenium script `{SELENIUM_SCRIPT_NAME}` not found in project root. Place it there to enable FB scraping.")
                else:
                    st.warning("This will attempt to execute a local Selenium script as a subprocess. It requires chromedriver and will open a browser window for you to login to Facebook. Use only locally.")
                    chromedriver_path = st.text_input("Local chromedriver path (full path)", value="", key="chromedriver_path_csv")
                    if not chromedriver_path:
                        st.error("Provide chromedriver path to run FB script.")
                    else:
                        # Write a temporary CSV input for the script to read (so the script can behave similarly to your original)
                        tmp_input = "tmp_outreach_input.csv"
                        df.to_csv(tmp_input, index=False)
                        # Run subprocess: user script should read tmp_outreach_input.csv and write tmp_outreach_output.csv
                        try:
                            proc = subprocess.Popen(["python", SELENIUM_SCRIPT_NAME, tmp_input, chromedriver_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                            st.info("Selenium script started as subprocess. Check terminal window for interactive login prompt; Streamlit may not show interactive login.")
                            stdout, stderr = proc.communicate()
                            st.text("Selenium script stdout:")
                            st.text(stdout)
                            if stderr:
                                st.text("Selenium script stderr:")
                                st.text(stderr)
                            # read output if produced
                            if os.path.exists("tmp_outreach_output.csv"):
                                out_df = pd.read_csv("tmp_outreach_output.csv")
                                st.dataframe(out_df.head(50))
                                st.download_button("Download FB-scraped CSV", data=out_df.to_csv(index=False).encode("utf-8"), file_name="fb_scraped_output.csv", mime="text/csv")
                            else:
                                st.warning("Selenium script did not produce tmp_outreach_output.csv. Check script behavior.")
                        except Exception as e:
                            st.error(f"Failed to run selenium script: {e}")

    else:
        st.info("Google Sheets mode will connect to `OutreachLog`. Upload the service-account JSON and authorize.")
        uploaded_key = st.file_uploader("Upload service-account JSON (keep private)", type=["json"], key="email_servicekey")
        sheet_name = st.text_input("Google Spreadsheet name (default: OutreachLog)", value="OutreachLog", key="email_sheetname")
        leads_ws_name = st.text_input("Leads worksheet name (default: OutreachLeads)", value="OutreachLeads", key="email_leadsname")
        operate = st.checkbox("Allow writing back found emails to Google Sheets (will overwrite Email column)", value=False, key="email_operate")
        run_button = st.button("Preview emails from Google Sheet", key="email_run")

        if run_button:
            if not uploaded_key:
                st.error("Please upload the service-account JSON file.")
            else:
                key_path = os.path.join(".", uploaded_key.name)
                with open(key_path, "wb") as f:
                    f.write(uploaded_key.getbuffer())
                try:
                    import gspread
                    from oauth2client.service_account import ServiceAccountCredentials
                except Exception as e:
                    st.error("Missing libraries: please `pip install gspread oauth2client`. Error: " + str(e))
                    st.stop()
                scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                creds = ServiceAccountCredentials.from_json_keyfile_name(key_path, scope)
                client = gspread.authorize(creds)
                try:
                    sh = client.open(sheet_name)
                    leads_ws = sh.worksheet(leads_ws_name)
                except Exception as e:
                    st.error(f"Failed to open sheet/worksheet: {e}")
                    st.stop()
                rows = leads_ws.get_all_values()
                if not rows or len(rows) < 2:
                    st.error("No data (or only header) found in worksheet.")
                else:
                    headers = rows[0]
                    data_rows = rows[1:]
                    df = pd.DataFrame(data_rows, columns=headers)
                    st.write("Preview of sheet (first 10 rows):")
                    st.dataframe(df.head(10))

                    # detect IG / email columns
                    email_col = None
                    for c in ["Email", "E-mail", "email", "Email Address"]:
                        if c in df.columns:
                            email_col = c
                            break
                    ig_col = None
                    for c in ["IG", "Instagram", "IG Link", "ig_link", "Instagram URL"]:
                        if c in df.columns:
                            ig_col = c
                            break
                    st.write("Detected columns:", {"email_col": email_col, "ig_col": ig_col})

                    # Run IG scraping
                    if run_ig:
                        st.info("Running IG scraping for rows missing email...")
                        results = []
                        for idx, row in df.iterrows():
                            cur_email = str(row.get(email_col, "")).strip() if email_col else ""
                            if cur_email:
                                results.append(cur_email)
                                continue
                            ig_url = row.get(ig_col, "") if ig_col else ""
                            if not ig_url or pd.isna(ig_url):
                                results.append("")
                                continue
                            try:
                                found = scrape_instagram_bio(ig_url)
                                results.append(found[0] if found else "")
                            except Exception as e:
                                results.append("")
                                st.warning(f"Row {idx+2}: IG scrape error: {e}")  # +2 to reflect sheet row
                        df_result = df.copy()
                        if email_col:
                            df_result[email_col] = results
                        else:
                            df_result["Found Email"] = results
                        st.markdown("### Results (first 50 rows)")
                        st.dataframe(df_result.head(50))
                        csv_bytes = df_result.to_csv(index=False).encode("utf-8")
                        st.download_button("Download CSV with found emails", data=csv_bytes, file_name="Outreach_with_emails.csv", mime="text/csv")

                        # optionally write back
                        if operate:
                            if st.button("Write found emails back to Google Sheet (Confirm)", key="email_write"):
                                try:
                                    col_map = {key: headers.index(key) for key in headers}
                                    for idx0, val in enumerate(results):
                                        if not val:
                                            continue
                                        sheet_row = idx0 + 2
                                        if email_col:
                                            leads_ws.update_cell(sheet_row, col_map[email_col] + 1, val)
                                        else:
                                            # if email col missing, warn and skip write
                                            st.warning("No email column found; cannot write back without a column named 'Email'.")
                                            break
                                    st.success("Attempted to write found emails back to sheet.")
                                except Exception as e:
                                    st.error(f"Failed to write back found emails: {e}")

                # cleanup
                try:
                    if os.path.exists(key_path):
                        os.remove(key_path)
                except Exception:
                    pass

    st.markdown("---")
    st.caption("If you plan to run FB scraping, it's safer to run your Selenium script locally in a terminal window (the script you pasted earlier). The 'run FB' subprocess trigger in CSV mode is a convenience but may not work in all environments; run locally for best results.")

# -------------------------
# TAB 3: About / Run Notes
# -------------------------
with tabs[2]:
    st.header("About & Run Notes")
    st.markdown(
        """
        * IG scraping uses `requests` and `BeautifulSoup` and is safe to run from Streamlit.
        * FB scraping uses Selenium and requires a local chromedriver and manual login; this is NOT recommended for cloud deployments.
        * To enable Selenium FB scraping via the UI:
          1. Place your Selenium script in project root and name it `fb_email_scraper.py` (or edit SELENIUM_SCRIPT_NAME above).
          2. Ensure the script accepts input CSV path and chromedriver path as arguments, writes output CSV `tmp_outreach_output.csv`.
          3. Provide full chromedriver path in the UI and run the FB subprocess.
        * If you want, I can adapt your Selenium script to accept a CSV input path and produce a CSV output — tell me and I'll update it now.
        """
    )

st.caption("All done. If you want: next I can (pick one):\n - adapt your Selenium script to accept input/output CSV paths, OR\n - change the FB subprocess invocation to use a safer, configurable interface, OR\n - prepare a minimal Dockerfile for local deployment (note: Selenium in Docker requires extra setup).")
