"""
Configuration loader for the outreach automation system.
Loads all environment variables from .env file.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class Config:
    """Centralized configuration management"""
    
    # Instagram Credentials
    INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
    INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

    OUTREACH=os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
    
    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv(
        "GOOGLE_SHEETS_CREDENTIALS_PATH",
        "OUTREACH"
    )
    GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "OutreachLog")
    
    # Personal Information
    YOUR_NAME = os.getenv("YOUR_NAME", "Girinath")
    YOUR_CITY = os.getenv("YOUR_CITY", "Chennai")
    YOUR_BRAND = os.getenv("YOUR_BRAND", "BlakShyft")
    YOUR_PORTFOLIO = os.getenv("YOUR_PORTFOLIO", "https://yourportfolio.com")
    
    # Selenium/ChromeDriver
    CHROMEDRIVER_PATH = os.getenv(
        "CHROMEDRIVER_PATH",
        "chromedriver.exe"
    )
    
    # Tesseract OCR
    TESSERACT_PATH = os.getenv(
        "TESSERACT_PATH",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )
    
    # Optional: OpenAI API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Google Sheets Scopes
    GOOGLE_SHEETS_SCOPES = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    @classmethod
    def validate(cls):
        """Validate that all required credentials are present"""
        required = {
            "INSTAGRAM_USERNAME": cls.INSTAGRAM_USERNAME,
            "INSTAGRAM_PASSWORD": cls.INSTAGRAM_PASSWORD,
            "GOOGLE_SHEETS_CREDENTIALS_PATH": cls.GOOGLE_SHEETS_CREDENTIALS_PATH,
        }
        
        missing = [key for key, value in required.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please check your .env file."
            )
        
        # Check if Google credentials file exists
        if not Path(cls.GOOGLE_SHEETS_CREDENTIALS_PATH).exists():
            raise FileNotFoundError(
                f"Google credentials file not found: {cls.GOOGLE_SHEETS_CREDENTIALS_PATH}"
            )
        
        print("✅ All configuration validated successfully!")
        return True


# Validate configuration on import (optional, comment out if you want manual validation)
# Config.validate()