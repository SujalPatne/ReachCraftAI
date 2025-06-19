#!/bin/bash

echo "--- Creating directories ---"
mkdir -p templates
mkdir -p uploads
echo "Directories 'templates' and 'uploads' created (or already exist)."

echo "--- Updating .gitignore ---"
# Ensure uploads/ is in .gitignore
if [ -f .gitignore ]; then
    grep -qxF 'uploads/' .gitignore || echo 'uploads/' >> .gitignore
    echo ".gitignore checked/updated for 'uploads/'."
else
    # If .gitignore doesn't exist, create it with common ignores + uploads/
    echo "__pycache__/" > .gitignore
    echo "*.pyc" >> .gitignore
    echo "*.db" >> .gitignore
    echo "venv/" >> .gitignore
    echo ".env" >> .gitignore
    echo "instance/" >> .gitignore
    echo "uploads/" >> .gitignore
    echo ".vscode/" >> .gitignore
    echo "*.log" >> .gitignore
    echo "*.sh" >> .gitignore # Add shell scripts like this one
    echo ".gitignore created with default entries and 'uploads/'."
fi

# Create templates/index.html using a HERE document
echo "--- Creating templates/index.html ---"
cat > templates/index.html << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Automation Control Panel</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        .container { background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        label { display: block; margin-top: 15px; margin-bottom: 5px; font-weight: bold; }
        input[type="file"], textarea, input[type="submit"] { width: 100%; padding: 10px; margin-bottom: 10px; border-radius: 4px; border: 1px solid #ddd; box-sizing: border-box; }
        textarea { min-height: 100px; resize: vertical; }
        input[type="submit"] { background-color: #007bff; color: white; font-weight: bold; cursor: pointer; border: none; }
        input[type="submit"]:hover { background-color: #0056b3; }
        .links { margin-top: 20px; padding-top: 10px; border-top: 1px solid #eee; }
        .links a { margin-right: 15px; color: #007bff; text-decoration: none; }
        .links a:hover { text-decoration: underline; }
        .status-info { margin-top: 10px; padding: 10px; background-color: #e9ecef; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Email Automation Control Panel</h1>

        <form action="/process-emails" method="post" enctype="multipart/form-data">
            <div>
                <label for="csv_file">Upload CSV File:</label>
                <input type="file" id="csv_file" name="csv_file" accept=".csv" required>
            </div>

            <div>
                <label for="prompt">Email Generation Prompt:</label>
                <textarea id="prompt" name="prompt" rows="5" required placeholder="e.g., Write a welcome email to {Company Name}. Mention their work in the {Industry} sector..."></textarea>
                <small>Use placeholders like {Company Name}, {Email}, or any other column header from your CSV.</small>
            </div>

            <input type="submit" value="Process and Send Emails">
        </form>

        <div class="links">
            <h3>Test Routes & Info:</h3>
            <a href="/view-data" target="_blank">View Raw CSV Data (from pre-configured export_50.csv)</a><br>
            <a href="/generate-test-email?company=TestCorp" target="_blank">Test Email Generation</a><br>
            <a href="/send-test-email?recipient=test@example.com" target="_blank">Test Email Sending</a>
        </div>
        <div class="status-info">
            <p>Debug Mode: {{ debug_mode }}</p>
            <p>Pre-configured CSV Path (for /view-data): {{ csv_path }}</p>
            <p>Gemini API Configured: {{ gemini_configured }}</p>
            <p>SMTP Configured: {{ smtp_configured }}</p>
        </div>
    </div>
</body>
</html>
EOF
echo "templates/index.html created."

# Update app.py using a HERE document
echo "--- Updating app.py ---"
cat > app.py << EOF
from flask import Flask, jsonify, request, render_template # Added render_template
import os
import werkzeug.utils # For secure_filename

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


# Dummy/fallback imports (as before)
try:
    from excel_processor import extract_data_from_csv
    print("Successfully imported extract_data_from_csv.")
except ImportError:
    print("Warning: excel_processor.py not found. Using dummy extract_data_from_csv.")
    def extract_data_from_csv(file_path, **kwargs): return [{"Email": "dummy_excel@example.com", "Company Name": "Dummy Excel Corp"}]
try:
    from email_generator import generate_email_content
    print("Successfully imported generate_email_content.")
except ImportError:
    print("Warning: email_generator.py not found. Using dummy generate_email_content.")
    def generate_email_content(company_data, user_prompt): return "Dummy email content from dummy_generator."
try:
    from email_sender import send_email
    print("Successfully imported send_email.")
except ImportError:
    print("Warning: email_sender.py not found. Using dummy send_email.")
    def send_email(recipient_email, subject, body): return False, "Dummy sending failed (sender not found)."

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SECRET_KEY
app.config['DEBUG'] = settings.DEBUG
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# This is for the /view-data route, using the pre-existing file specified in config
PRECONFIGURED_CSV_FILE_PATH = settings.CSV_FILE_PATH

@app.route('/')
def index_route():
    return render_template('index.html',
                           debug_mode=app.config['DEBUG'],
                           csv_path=PRECONFIGURED_CSV_FILE_PATH, # Show path of preconfigured CSV
                           gemini_configured="Yes" if settings.GEMINI_API_KEY else "No",
                           smtp_configured="Yes" if settings.SMTP_HOST else "No"
                           )

@app.route('/process-emails', methods=['POST'])
def process_emails_route():
    if 'csv_file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    file = request.files['csv_file']
    prompt = request.form.get('prompt', '')

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    if file and file.filename.endswith('.csv'):
        try:
            filename = werkzeug.utils.secure_filename(file.filename)
            uploaded_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(uploaded_filepath)

            # Placeholder: actual processing will use uploaded_filepath
            print(f"File {filename} uploaded to {uploaded_filepath}. Prompt: '{prompt}'")
            # Here, you would call extract_data_from_csv(uploaded_filepath),
            # then loop through data, call generate_email_content, then send_email.
            # This is simplified for now.
            return jsonify({
                "message": "File and prompt received. Placeholder for processing.",
                "uploaded_filename": filename,
                "prompt_received": prompt,
                "status": "Received, processing not yet implemented."
            })
        except Exception as e:
            print(f"Error during file upload or placeholder processing: {str(e)}")
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    else:
        return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400

# Existing test routes
@app.route('/view-data')
def view_data_route():
    if not os.path.exists(PRECONFIGURED_CSV_FILE_PATH):
        return jsonify({"error": f"Preconfigured CSV file not found at {PRECONFIGURED_CSV_FILE_PATH}"}), 404
    processed_data = extract_data_from_csv(PRECONFIGURED_CSV_FILE_PATH)
    if not processed_data:
        if os.path.exists(PRECONFIGURED_CSV_FILE_PATH):
             return jsonify({"message": "CSV file processed, but no data was extracted.", "data": []})
        return jsonify({"error": "Failed to extract data from CSV or file is empty."}), 500
    return jsonify(processed_data)

@app.route('/generate-test-email')
def generate_test_email_route():
    company_name_from_query = request.args.get('company', 'Default Test Company')
    sample_company_data = {"Company Name": company_name_from_query, "Industry": "Various"}
    fixed_prompt = "Write a short, friendly welcome email to {Company Name}."
    email_body = generate_email_content(sample_company_data, fixed_prompt)
    return f"<h1>Test Email Generation</h1><p><b>To:</b> {company_name_from_query}</p><p><b>Prompt:</b> {fixed_prompt}</p><hr><pre>{email_body}</pre>"

@app.route('/send-test-email')
def send_test_email_route():
    recipient = request.args.get('recipient')
    if not recipient:
        return jsonify({"error": "Missing 'recipient' query parameter."}), 400
    test_company_data = {"Company Name": "TestCo via AppRoute"}
    test_prompt = "Generate a very brief test email for {Company Name}."
    email_subject = "Test Email from Flask App"
    email_body = generate_email_content(test_company_data, test_prompt)
    if "Error:" in email_body or "Dummy" in email_body: # Check for errors or dummy content
        email_subject = "Fallback Test Email from Flask App (Generator Issue)"
        email_body = f"<p>Hello {recipient},</p><p>This is a test email. Generator Output: {email_body}</p>"
    success, message = send_email(recipient, email_subject, email_body)
    if success:
        return jsonify({"status": "success", "message": message})
    else:
        return jsonify({"status": "failure", "message": message}), 500

if __name__ == '__main__':
    print("Attempting to start Flask app with UI and processing endpoint...")
    try:
        app.run(host='0.0.0.0', port=8080)
    except ImportError as e:
        print(f"ImportError: {e}. Ensure Flask and Werkzeug are available.")
    except Exception as e:
        print(f"Failed to start Flask app: {e}")
EOF
echo "app.py updated."

# Add werkzeug to requirements.txt
echo "--- Updating requirements.txt for Werkzeug ---"
grep -qxF 'Werkzeug' requirements.txt || echo 'Werkzeug' >> requirements.txt
cat requirements.txt
echo "Werkzeug check/add to requirements.txt complete."

echo "--- Script finished ---"
echo "templates/index.html created."
echo "uploads/ directory created and .gitignore updated."
echo "app.py updated for UI and /process-emails route."
echo "Testing is still not possible due to Flask/pip issues."
