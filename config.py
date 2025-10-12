import os
import pytz

class Config:
    # ========================
    # WHATSAPP API CONFIG
    # ========================
    VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "dwainz_verify")
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "839043219287688")
    BUSINESS_DISPLAY_NUMBER = "+15551442247"
    
    # ========================
    # DATABASE CONFIG
    # ========================
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # ========================
    # ANONYMIZATION CONFIG
    # ========================
    CLIENT_ID_PREFIX = "CL"
    CLIENT_STAFF_PREFIX = "CS"  
    VENDOR_STAFF_PREFIX = "VS"
    VENDOR_ID_PREFIX = "V"
    
    # ========================
    # BUSINESS RULES
    # ========================
    DEAL_AUTO_CLOSE_DAYS = 3  # Default 3-day timeout
    TIMEZONE = pytz.timezone("Africa/Lagos")
