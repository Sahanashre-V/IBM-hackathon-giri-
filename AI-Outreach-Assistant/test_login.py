"""
Instagram Login Script using Instagrapi
Uses credentials from .env file for security
"""
from instagrapi import Client
from config import Config
import json

# Validate configuration
Config.validate()

def login_instagram():
    """Login to Instagram and save session"""
    cl = Client()
    
    print("🔐 Attempting Instagram login...")
    
    # Try to load existing session
    try:
        cl.load_settings("insta_session.json")
        cl.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
        print("[✓] Logged in using saved session.")
        return cl
    except Exception as e:
        print(f"[!] Session load failed: {e}")
        print("[!] Trying fresh login...")
    
    # Fresh login attempt
    try:
        cl.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
        print("[✓] Fresh login successful.")
        
        # Save session for future use
        cl.dump_settings("insta_session.json")
        print("[✓] Session saved to 'insta_session.json'")
        return cl
        
    except Exception as e:
        print(f"[!] Fresh login failed: {e}")
        print("[!] Trying OTP method...")
        
        # OTP method
        try:
            cl.send_code(Config.INSTAGRAM_USERNAME)
            code = input("[?] Enter the code you received: ")
            cl.login(
                Config.INSTAGRAM_USERNAME,
                Config.INSTAGRAM_PASSWORD,
                verification_code=code
            )
            print("[✓] Login via OTP successful.")
            
            # Save session
            cl.dump_settings("insta_session.json")
            print("[✓] Session saved to 'insta_session.json'")
            return cl
            
        except Exception as otp_err:
            print(f"[✗] OTP login failed: {otp_err}")
            raise

def test_login():
    """Test the login and verify it works"""
    try:
        cl = login_instagram()
        
        # Verify login by getting user ID
        user_id = cl.user_id_from_username(Config.INSTAGRAM_USERNAME)
        print(f"[✓] Successfully logged in as ID: {user_id}")
        
        # Get user info
        user_info = cl.user_info(user_id)
        print(f"[✓] Account: @{user_info.username}")
        print(f"[✓] Followers: {user_info.follower_count}")
        print(f"[✓] Following: {user_info.following_count}")
        
        return cl
        
    except Exception as e:
        print(f"[✗] Login test failed: {e}")
        return None

if __name__ == "__main__":
    client = test_login()
    
    if client:
        print("\n✅ Instagram client ready to use!")
        print("💡 You can now use this client in other scripts for scraping.")
    else:
        print("\n❌ Login failed. Please check your credentials in .env file.")