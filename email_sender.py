import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart # For more complex emails later if needed
import sys # For printing to stderr

# Attempt to import settings from config.py
try:
    from config import settings # Import shared SMTP settings
    print("Successfully imported settings from config.")
except ImportError:
    print("Error: Could not import settings from config.py. Ensure config.py exists and is accessible.", file=sys.stderr)
    # Define a dummy settings object for the script to be syntactically valid if config is missing
    class DummySettings:
        SMTP_HOST = None
        SMTP_PORT = 587
        SMTP_SENDER_EMAIL = None
        SMTP_USERNAME = None
        SMTP_PASSWORD = None
        SMTP_USE_TLS = True
        GEMINI_API_KEY = None # Added for the __main__ block check consistency
    settings = DummySettings()


def send_email(recipient_email, subject, body):
    """
    Sends an email using SMTP settings from config.py.

    Args:
        recipient_email (str): The email address of the recipient.
        subject (str): The subject of the email.
        body (str): The HTML or plain text body of the email.

    Returns:
        bool: True if email was sent successfully, False otherwise.
        str: A message indicating success or failure.
    """
    if not all([settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_SENDER_EMAIL]):
        msg = "Error: SMTP configuration (HOST, PORT, SENDER_EMAIL) is incomplete in settings."
        print(msg, file=sys.stderr)
        return False, msg

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.SMTP_SENDER_EMAIL
    message["To"] = recipient_email

    html_part = MIMEText(body, "html")
    message.attach(html_part)

    try:
        print(f"Attempting to connect to SMTP: {settings.SMTP_HOST}:{settings.SMTP_PORT}", file=sys.stderr)
        if settings.SMTP_USE_TLS:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) # Added timeout
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) # Added timeout

        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            print(f"Attempting SMTP login for user: {settings.SMTP_USERNAME}", file=sys.stderr)
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

        print(f"Sending email to: {recipient_email} from: {settings.SMTP_SENDER_EMAIL}", file=sys.stderr)
        server.sendmail(settings.SMTP_SENDER_EMAIL, recipient_email, message.as_string())
        server.quit()

        success_msg = f"Email sent successfully to {recipient_email}."
        print(success_msg) # Print success to stdout for user
        return True, success_msg

    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP Authentication Error for user {settings.SMTP_USERNAME}: {e}"
        print(error_msg, file=sys.stderr)
        return False, error_msg
    except smtplib.SMTPServerDisconnected as e:
        error_msg = f"SMTP Server Disconnected: {e}. Check server address ({settings.SMTP_HOST}) and port ({settings.SMTP_PORT})."
        print(error_msg, file=sys.stderr)
        return False, error_msg
    except smtplib.SMTPConnectError as e:
        error_msg = f"SMTP Connection Error: Could not connect to {settings.SMTP_HOST}:{settings.SMTP_PORT}. Error: {e}"
        print(error_msg, file=sys.stderr)
        return False, error_msg
    except Exception as e: # Catch-all for other smtplib errors or general errors
        error_msg = f"An unexpected error occurred while sending email via {settings.SMTP_HOST}: {e}"
        print(error_msg, file=sys.stderr)
        return False, error_msg

if __name__ == '__main__':
    print("--- Email Sender Test ---")

    # Check critical settings required for a meaningful test (even dry run)
    essential_smtp_config = all([settings.SMTP_HOST, settings.SMTP_SENDER_EMAIL])
                                 # settings.SMTP_PORT has a default, so it's always "set"

    if not essential_smtp_config:
        print("Skipping test: Essential SMTP settings (HOST, SENDER_EMAIL) are not configured.")
        print(f"Current SMTP Host: {settings.SMTP_HOST}")
        print(f"Current SMTP Port: {settings.SMTP_PORT}")
        print(f"Current SMTP Sender Email: {settings.SMTP_SENDER_EMAIL}")
    else:
        print("Attempting to send a test email (dry run simulation unless fully configured and network accessible)...")
        test_recipient = "test@example.com"
        test_subject = "Test Email from Email Sender Script"
        test_body = "<h1>Hello!</h1><p>This is a <b>test email</b> sent from the <code>email_sender.py</code> script.</p>"

        print(f"Test Recipient: {test_recipient}")
        print(f"Test Subject: {test_subject}")
        print(f"Test Body (first 50 chars): {test_body[:50]}...")

        print("\n--- Simulating send_email call ---")
        print(f"Would use SMTP Host: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        print(f"Would use Sender Email: {settings.SMTP_SENDER_EMAIL}")
        if settings.SMTP_USERNAME:
            print(f"Would login with Username: {settings.SMTP_USERNAME}")
        print(f"TLS Enabled: {settings.SMTP_USE_TLS}")
        print("--- End of Dry Run Simulation ---")

        # To actually send (USE WITH CAUTION AND REAL CREDENTIALS IN A SECURE .env):
        # print("\n--- !!! Uncomment below to attempt ACTUAL email sending !!! ---")
        # success, message = send_email(test_recipient, test_subject, test_body)
        # print(f"\nActual Send Attempt Status: {success} - {message}")
