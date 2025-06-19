import os
from dotenv import load_dotenv

# Load .env file from the root directory
# Assuming config.py is in the root directory for this setup.
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
# A common pattern: if __file__ is just 'config.py' (no dir part), it means script is run from same dir as .env
if os.path.basename(os.path.dirname(__file__)) == '' and not os.path.exists(dotenv_path):
    # Fallback for when script is in root and run from root, and .env is also in root.
    # In this case, os.path.dirname(__file__) is empty.
    dotenv_path = '.env'

if not os.path.exists(dotenv_path):
    print(f"Warning: .env file not found at '{dotenv_path}'. Looked for it relative to config.py and as fallback in CWD if config.py is in CWD. Using environment variables or defaults.")
else:
    print(f"Loading .env file from: {os.path.abspath(dotenv_path)}") # Show absolute path for clarity
    load_dotenv(dotenv_path)

class Settings:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-secure-default-secret-key-please-change'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

    # Gemini API Key
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

    # SMTP Settings
    SMTP_HOST = os.environ.get('SMTP_HOST')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587)) # Default to 587 if not set
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    SMTP_SENDER_EMAIL = os.environ.get('SMTP_SENDER_EMAIL') # 'From' email address
    SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'True').lower() in ('true', '1', 't')

    # CSV File Path (can also be configured here)
    CSV_FILE_PATH = os.environ.get('CSV_FILE_PATH') or 'export_50.csv'

    # Basic check for essential configs
    # These print statements will execute when the module is imported.
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY is not set in environment or .env file.")
    if not SMTP_HOST:
        print("Warning: SMTP_HOST is not set. Email sending will likely fail.")

# Instantiate settings to be imported by other modules
settings = Settings()

if __name__ == '__main__':
    # For testing the config loading
    print("--- Configuration Test ---")
    print(f"Flask Debug: {settings.DEBUG}")
    print(f"Gemini API Key Loaded: {'Yes' if settings.GEMINI_API_KEY else 'No'}")
    print(f"SMTP Host: {settings.SMTP_HOST}")
    print(f"SMTP Port: {settings.SMTP_PORT}")
    print(f"SMTP Username: {settings.SMTP_USERNAME}")
    print(f"SMTP Sender Email: {settings.SMTP_SENDER_EMAIL}")
    print(f"CSV File Path: {settings.CSV_FILE_PATH}")
    if settings.GEMINI_API_KEY:
        print(f"Gemini Key (first 5 chars): {settings.GEMINI_API_KEY[:5]}...")
    # Test .env loading message
    print(f"\n--- .env Loading Test ---")
    # Create a dummy .env for this test if it doesn't exist, to check dotenv_path logic
    test_dotenv_path = '.env' # Path where config.py expects .env when run from root
    if not os.path.exists(test_dotenv_path):
        print(f"'{test_dotenv_path}' not found, creating a dummy one for test...")
        with open(test_dotenv_path, 'w') as f:
            f.write("TEST_VAR_DOTENV='loaded_from_dummy_env'\n")
        # Re-run load_dotenv for the purpose of this test block
        # This is a bit artificial as Settings class is already defined
        # A better test would be to instantiate Settings again or check a var
        load_dotenv(test_dotenv_path)
        print(f"TEST_VAR_DOTENV from os.environ: {os.environ.get('TEST_VAR_DOTENV')}")
        if os.path.exists(test_dotenv_path): # Check again before removing
             os.remove(test_dotenv_path) # Clean up dummy
    else:
        # If .env exists, show a variable from it if possible (e.g. SECRET_KEY)
        print(f"Existing '{test_dotenv_path}' found. SECRET_KEY (should be loaded): {os.environ.get('SECRET_KEY')}")
