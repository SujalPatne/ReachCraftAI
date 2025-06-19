from flask import Flask, jsonify, request, render_template
import os
import werkzeug.utils
import csv # For logging and reading stats
from datetime import datetime # For timestamping logs

# Import settings from config.py, assuming it's in the same directory (root)
try:
    from config import settings
    print("Successfully imported settings from config.")
except ImportError:
    print("Error: Could not import settings from config.py. Using dummy settings.")
    class DummySettings: # Define a fallback if config.py is missing
        SECRET_KEY = 'dummy-secret-key'
        DEBUG = True
        CSV_FILE_PATH = 'export_50.csv' # Default path
        GEMINI_API_KEY = None
        SMTP_HOST = None
    settings = DummySettings()

# Dummy/fallback imports
try:
    from excel_processor import extract_data_from_csv
    print("Successfully imported extract_data_from_csv from excel_processor.")
except ImportError:
    print("Warning: excel_processor.py not found. Using dummy extract_data_from_csv.")
    def extract_data_from_csv(file_path, **kwargs):
        print(f"Dummy excel_processor.extract_data_from_csv called for {file_path}")
        return [{"Email": "dummy1@example.com", "Company Name": "Dummy Corp 1", "Status": "Processed", "Industry": "Tech"},
                {"Email": "dummy2@example.com", "Company Name": "Dummy Corp 2", "Status": "Processed", "Industry": "Retail"},
                {"Email": "", "Company Name": "No Email Corp", "Status": "Processed", "Industry": "Services"}]
try:
    from email_generator import generate_email_content
    print("Successfully imported generate_email_content from email_generator.")
except ImportError:
    print("Warning: email_generator.py not found. Using dummy generate_email_content.")
    def generate_email_content(company_data, user_prompt):
        print(f"Dummy email_generator.generate_email_content for {company_data.get('Company Name')}")
        filled_prompt = user_prompt.format(**company_data)
        return f"Dummy email content for {company_data.get('Company Name')} based on prompt: '{filled_prompt}'"
try:
    from email_sender import send_email
    print("Successfully imported send_email from email_sender.")
except ImportError:
    print("Warning: email_sender.py not found. Using dummy send_email.")
    def send_email(recipient_email, subject, body):
        print(f"Dummy email_sender.send_email to {recipient_email} with subject '{subject}'")
        if "dummy2" in recipient_email: return False, "Dummy sending failed for dummy2."
        return True, "Dummy email sent successfully."

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SECRET_KEY
app.config['DEBUG'] = settings.DEBUG
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

PRECONFIGURED_CSV_FILE_PATH = settings.CSV_FILE_PATH # For /view-data
LOG_FILE_PATH = 'sent_emails.log.csv'

# --- Logging Function ---
def log_email_attempt(recipient, subject, status, message):
    """Appends a record to the email log CSV file."""
    file_exists = os.path.isfile(LOG_FILE_PATH)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE_PATH, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'recipient', 'subject', 'status', 'message']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists or os.path.getsize(LOG_FILE_PATH) == 0: # Check size for empty file too
                writer.writeheader() # Write header if file is new or empty
            writer.writerow({
                'timestamp': now,
                'recipient': recipient,
                'subject': subject,
                'status': status,
                'message': message
            })
    except Exception as e:
        print(f"Error writing to log file {LOG_FILE_PATH}: {e}")

# --- Routes ---
@app.route('/')
def index_route():
    return render_template('index.html',
                           debug_mode=app.config['DEBUG'],
                           csv_path=PRECONFIGURED_CSV_FILE_PATH,
                           gemini_configured="Yes" if settings.GEMINI_API_KEY else "No",
                           smtp_configured="Yes" if settings.SMTP_HOST else "No",
                           log_file_exists=os.path.exists(LOG_FILE_PATH)
                           )

@app.route('/process-emails', methods=['POST'])
def process_emails_route():
    if 'csv_file' not in request.files: return jsonify({"error": "No file part"}), 400
    file = request.files['csv_file']
    prompt_template = request.form.get('prompt', '')
    if file.filename == '': return jsonify({"error": "No selected file"}), 400
    if not prompt_template: return jsonify({"error": "Prompt template required"}), 400

    if file and file.filename.endswith('.csv'):
        try:
            filename = werkzeug.utils.secure_filename(file.filename)
            uploaded_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(uploaded_filepath)

            print(f"File '{filename}' uploaded to '{uploaded_filepath}'. Processing with prompt: '{prompt_template}'")
            contacts = extract_data_from_csv(uploaded_filepath)
            if not contacts:
                msg = f"No data extracted from {filename}. Check file content or column names."
                print(msg)
                log_email_attempt("N/A", "Batch Processing Error", "Failed", msg)
                return jsonify({"error": msg}), 400

            results = []
            emails_sent_count = 0
            emails_failed_count = 0

            for contact_data in contacts:
                recipient_email = contact_data.get("Email")
                company_name = contact_data.get("Company Name") if contact_data.get("Company Name") else "Valued Partner"
                subject = f"Regarding Your Business, {company_name}"

                if not recipient_email or not isinstance(recipient_email, str) or "@" not in recipient_email:
                    reason = "Missing or invalid email address in CSV row."
                    print(f"Skipping contact ({company_name}) due to: {reason}")
                    log_email_attempt(recipient_email or "N/A", subject, "Failed", reason)
                    results.append({"recipient": recipient_email or "N/A", "company": company_name, "status": "Failed", "reason": reason})
                    emails_failed_count += 1
                    continue

                try:
                    email_body = generate_email_content(contact_data, prompt_template)
                except KeyError as e_key:
                    reason = f"Prompt formatting error: Missing key {e_key}. Ensure all prompt placeholders match CSV headers."
                    print(f"Email generation failed for {recipient_email}: {reason}")
                    log_email_attempt(recipient_email, subject, "Failed", reason)
                    results.append({"recipient": recipient_email, "company": company_name, "status": "Failed", "reason": reason})
                    emails_failed_count += 1
                    continue

                if "Error:" in email_body or ("Dummy email content" in email_body and "dummy_generator" in email_body):
                    reason = f"Email content generation issue: {email_body}"
                    print(f"Email generation failed or used dummy for {recipient_email}: {reason}")
                    log_email_attempt(recipient_email, subject, "Failed", reason)
                    results.append({"recipient": recipient_email, "company": company_name, "status": "Failed", "reason": reason})
                    emails_failed_count += 1
                    continue

                print(f"Attempting to send email to {recipient_email} for company {company_name}...")
                success, message = send_email(recipient_email, subject, email_body)
                log_status = "Sent" if success else "Failed"
                log_email_attempt(recipient_email, subject, log_status, message)

                if success:
                    emails_sent_count += 1
                    results.append({"recipient": recipient_email, "company": company_name, "status": "Sent", "message": message})
                else:
                    emails_failed_count += 1
                    results.append({"recipient": recipient_email, "company": company_name, "status": "Failed", "reason": message})

            summary_msg = "Email processing complete."
            print(f"{summary_msg} Sent: {emails_sent_count}, Failed: {emails_failed_count}")
            return jsonify({
                "message": summary_msg,
                "summary": {"total_contacts_processed": len(contacts), "emails_sent": emails_sent_count, "emails_failed": emails_failed_count},
                "details": results
            })
        except Exception as e:
            error_str = str(e)
            print(f"Error in /process-emails: {error_str}")
            log_email_attempt("N/A", "Batch Processing Error", "Failed", error_str)
            return jsonify({"error": f"An unexpected error occurred during processing: {error_str}"}), 500
    else:
        return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400

@app.route('/stats')
def stats_route():
    if not os.path.exists(LOG_FILE_PATH):
        return jsonify({"error": "Log file not found. No emails processed yet or logging failed."}), 404

    stats = {"total_attempts": 0, "successful_sends": 0, "failed_sends": 0, "recent_entries": []}
    try:
        with open(LOG_FILE_PATH, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # Check for header by trying to read fieldnames; if file is empty, fieldnames is None
            if not reader.fieldnames:
                return jsonify({"message": "Log file is empty.", "stats": stats}), 200

            # Normalize header names for checking
            normalized_log_headers = [name.strip().lower() for name in reader.fieldnames]
            if 'status' not in normalized_log_headers:
                 return jsonify({"error": "Log file has incorrect format (missing 'status' column)."}), 500

            log_entries = list(reader) # Read all entries
            stats["total_attempts"] = len(log_entries)

            for row in log_entries:
                # Ensure 'status' key exists in row before lowercasing, use .get for safety
                if row.get('status', '').strip().lower() == 'sent':
                    stats["successful_sends"] += 1
                else:
                    stats["failed_sends"] += 1

            # Get last 10 entries (or all if fewer than 10)
            stats["recent_entries"] = log_entries[-10:]

    except Exception as e:
        print(f"Error reading log file {LOG_FILE_PATH}: {e}")
        return jsonify({"error": f"Could not read or parse log file: {e}"}), 500

    return jsonify(stats)

# Existing test routes
@app.route('/view-data')
def view_data_route():
    if not os.path.exists(PRECONFIGURED_CSV_FILE_PATH): return jsonify({"error": f"CSV file not found at {PRECONFIGURED_CSV_FILE_PATH}"}), 404
    processed_data = extract_data_from_csv(PRECONFIGURED_CSV_FILE_PATH)
    if not processed_data:
        if os.path.exists(PRECONFIGURED_CSV_FILE_PATH): return jsonify({"message": "CSV file processed, but no data was extracted.", "data": []})
        return jsonify({"error": "Failed to extract data from CSV or file is empty."}), 500
    return jsonify(processed_data)

@app.route('/generate-test-email')
def generate_test_email_route():
    company_name_from_query = request.args.get('company', 'Default Test Company')
    sample_company_data = {"Company Name": company_name_from_query, "Industry": "Various", "Email": "test@example.com"}
    fixed_prompt = "Write a short, friendly welcome email to {Company Name} in the {Industry} sector. Their email is {Email}."
    email_body = generate_email_content(sample_company_data, fixed_prompt)
    return f"<h1>Test Email Generation</h1><p><b>To:</b> {company_name_from_query}</p><p><b>Prompt:</b> {fixed_prompt}</p><hr><pre>{email_body}</pre>"

@app.route('/send-test-email')
def send_test_email_route():
    recipient = request.args.get('recipient')
    if not recipient: return jsonify({"error": "Missing 'recipient' query parameter."}), 400
    test_company_data = {"Company Name": "TestCo via AppRoute", "Email": recipient, "Industry": "Testing"}
    test_prompt = "Generate a very brief test email for {Company Name} confirming the email system for {Email} is working."
    email_subject = "Test Email from Flask App"
    email_body = generate_email_content(test_company_data, test_prompt)

    # Log initial attempt for test sends
    log_email_attempt(recipient, email_subject, "Test - Attempted", "N/A (Test Route)")

    if "Error:" in email_body or "Dummy" in email_body:
        email_subject = "Fallback Test Email from Flask App (Generator Issue)"
        email_body = f"<p>Hello {recipient},</p><p>This is a test email. Generator Output: {email_body}</p>"

    success, message = send_email(recipient, email_subject, email_body)
    # Log final status for test sends
    log_email_attempt(recipient, email_subject, "Test - Sent" if success else "Test - Failed", message)

    if success: return jsonify({"status": "success", "message": message})
    else: return jsonify({"status": "failure", "message": message}), 500

if __name__ == '__main__':
    print("Attempting to start Flask app with logging and stats route...")
    try:
        app.run(host='0.0.0.0', port=8080)
    except ImportError as e:
        print(f"ImportError: {e}. Ensure Flask and dependencies are available.")
    except Exception as e:
        print(f"Failed to start Flask app: {e}")
