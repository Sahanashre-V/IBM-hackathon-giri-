import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === Setup Auth ===
OUTREACH=os.getenv(GOOGLE_SHEETS_CREDENTIALS_PATH)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "E:/IBM (Team - 7)/PROJECT/AI-Outreach-Assistant/${OUTREACH}", scope
)
client = gspread.authorize(creds)

# === Open Sheet ===
sheet = client.open("OutreachLog").sheet1  # Use your actual Sheet name if different

# === Example Data Entry ===
data = [
    "ZEG",                            # Name
    "Artist",                         # Role
    "Instagram",                      # Platform
    "https://instagram.com/zeg.p",    # Profile Link
    "",                               # Email
    "Acid x Bengaluru",               # Event Name
    "17 July"                         # Date
]

# === Append to Sheet ===
sheet.append_row(data)
print("✅ Entry added to Google Sheet.")