"""
Bulk PEC (Personalized Email Campaign) Generator
Reads leads from Google Sheets and generates personalized outreach messages
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from config import Config

# Validate configuration
Config.validate()

# ==== TEMPLATES ====
templates = {
    "artist_bad": """Hey {artist_name},

I'm {your_name}, a concert photographer from {city} running a visual brand called {brand}. I specialise in shooting clean, high-impact photos that really capture the energy of live sets.

I've noticed many artists, maybe even yourself often end up with great crowd videos but very few standout photographs that do justice to the vibe and lighting of the night. That's where I come in.

I've had the chance to work with names like Divyabharathi, DJ Soumya, and Premji, and would love to bring that same cinematic quality to your upcoming {event} show in {venue} on {date} (if you haven't already locked visuals). You can get a quick look here:
Portfolio: {portfolio}

Let me know if it's something you'd be open to. Happy to help if you're looking to build a strong post-event visual archive.

Cheers,  
{your_name}""",

    "artist_good": """Hey {artist_name},

I'm {your_name}, a concert photographer from {city} and founder of {brand}.

I saw your page and noticed you already have some great photos, but I think there's still a lot of room to push the visuals to an even more cinematic level, especially with your lighting setups.

I've worked with names like Divyabharathi, DJ Soumya, and Premji and would love to collaborate on your upcoming {event} show at {venue} on {date} if you're still open to visuals.

Portfolio: {portfolio}

Let me know if this sounds interesting!

Cheers,  
{your_name}""",

    "venue_bad": """Hey {artist_name},

I'm {your_name}, a concert photographer from {city} running a visual brand called {brand}. I specialise in shooting clean, high-impact photos that really capture the lighting and energy of events.

I've noticed that many venues, maybe even yours often have amazing light setups but don't have photographs that really showcase the vibe or scale of the space. That's where I come in.

I've worked with names like Divyabharathi, DJ Soumya, and Premji, and I'd love to bring that same cinematic quality to your upcoming {event} night on {date}. Here's a quick look:
Portfolio: {portfolio}

Let me know if this is something you'd be open to. Would love to collaborate.

Cheers,  
{your_name}""",

    "venue_good": """Hey {artist_name},

I'm {your_name}, a concert photographer from {city} running a visual brand called {brand}.

I checked out your page, love the energy, and the lighting looks insane. I think there's still room to elevate the visuals further and make your space stand out with more cinematic shots.

I've worked with names like Divyabharathi, DJ Soumya, and Premji, and I'd love to shoot your upcoming {event} night on {date} if you're open to it.

Portfolio: {portfolio}

Let me know if you'd like to talk more.

Cheers,  
{your_name}""",

    "curator_bad": """Hey {artist_name},

I'm {your_name}, a concert photographer from {city} and founder of a visual brand called {brand}. I specialise in capturing high-impact, clean visuals that reflect the real energy of your lineups and lighting.

I've noticed many event curators don't always get standout photos from their shows, especially ones that truly show off the production and crowd energy. I'd love to help change that.

I've worked with names like Divyabharathi, DJ Soumya, and Premji, and would love to shoot your upcoming {event} in {venue} on {date}.

Portfolio: {portfolio}

Let me know if it's something you'd be open to.

Cheers,  
{your_name}""",

    "curator_good": """Hey {artist_name},

I'm {your_name}, a concert photographer from {city} and founder of {brand}.

Your page already has some strong visuals, I think it's clear you care about the aesthetic. That said, there's always room to push it further into a more cinematic zone, especially with your crowd and lighting setups.

I've worked with names like Divyabharathi, DJ Soumya, and Premji and would love to collaborate on your upcoming {event} in {venue} on {date}.

Portfolio: {portfolio}

Let me know if this sounds interesting.

Cheers,  
{your_name}"""
}

def generate_bulk_messages():
    """Generate messages for all pending leads in the Google Sheet"""
    # Connect to Google Sheets
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        Config.GOOGLE_SHEETS_CREDENTIALS_PATH,
        Config.GOOGLE_SHEETS_SCOPES
    )
    client = gspread.authorize(creds)
    
    # Open the sheets
    sheet = client.open(Config.GOOGLE_SHEET_NAME).worksheet("OutreachLeads")
    
    rows = sheet.get_all_values()
    headers = rows[0]
    data_rows = rows[1:]

    # Get column indexes
    col_map = {key: headers.index(key) for key in headers}

    # Prepare output sheet
    try:
        output = client.open(Config.GOOGLE_SHEET_NAME).worksheet("GeneratedPECs")
    except:
        output = client.open(Config.GOOGLE_SHEET_NAME).add_worksheet(
            title="GeneratedPECs",
            rows="100",
            cols="2"
        )

    output.clear()
    output.append_row(["Name", "Generated PEC"])

    processed_count = 0
    skipped_count = 0

    for idx, row in enumerate(data_rows, start=2):
        status = row[col_map["Status"]].strip().lower()
        if status in ["sent", "replied"]:
            skipped_count += 1
            continue

        name = row[col_map["Name"]]
        event = row[col_map["Event"]]
        venue = row[col_map["Venue"]]
        date = row[col_map["Date"]]
        tag = row[col_map["Tag"]].strip()

        if tag not in templates:
            print(f"❌ Skipped row {idx}: Unknown tag '{tag}'")
            skipped_count += 1
            continue

        # Fill template with data
        data = {
            "artist_name": name,
            "your_name": Config.YOUR_NAME,
            "city": Config.YOUR_CITY,
            "brand": Config.YOUR_BRAND,
            "portfolio": Config.YOUR_PORTFOLIO,
            "event": event,
            "venue": venue,
            "date": date
        }

        message = templates[tag].format(**data)
        output.append_row([name, message])

        # Update status and timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.update_cell(idx, col_map["Status"] + 1, "Sent")
        sheet.update_cell(idx, col_map["Timestamp"] + 1, timestamp)
        
        processed_count += 1
        print(f"✅ Generated PEC for {name}")

    print(f"\n🎉 Done!")
    print(f"✅ Processed: {processed_count}")
    print(f"⏭️  Skipped: {skipped_count}")

if __name__ == "__main__":
    generate_bulk_messages()