# ReachCraftAI: Intelligently craft and automate personalized email outreach. 
Gemini-Powered Email Personalization App

## Overview

This application provides a web-based interface to send personalized emails to a list of contacts from a CSV file. It leverages the Gemini API to generate unique email content for each recipient based on a user-provided prompt template and data from the CSV. The application also features email sending capabilities via SMTP and logs all email sending attempts.

## Features

*   **Web Interface:** User-friendly interface built with Flask for uploading contacts and managing email campaigns.
*   **CSV Processing:** Reads contact details (Email, Company Name, and other custom fields) from a CSV file.
*   **Dynamic Email Generation:** Uses Google's Gemini API to craft personalized email bodies based on a customizable prompt template and contact-specific data.
*   **Email Sending:** Integrates with an SMTP server to send the generated emails.
*   **Logging:** Records the status (sent/failed) of each email attempt in `sent_emails.log.csv`.
*   **Statistics:** Provides a `/stats` endpoint to view a summary of email sending activities.
*   **Configuration:** Easy setup using a `.env` file for API keys and SMTP credentials.

## Workflow

1.  **Prepare Data:** Create a CSV file with contact information. Essential columns are for email and company name, but any other columns (e.g., "Industry", "Location") can be included and used in the prompt.
2.  **Configure Application:** Set up your `GEMINI_API_KEY` and SMTP details in the `.env` file.
3.  **Run Application:** Start the Flask server.
4.  **Use Web UI:**
    *   Open the application in your web browser.
    *   Upload your CSV file.
    *   Write a prompt template using placeholders for data from your CSV (e.g., `Dear {Company Name}, ...`).
    *   Submit the form to start the email generation and sending process.
5.  **Review Results:** The UI will display a summary of sent and failed emails. Detailed logs are available in `sent_emails.log.csv`.

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create a Python Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scriptsctivate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    *   Copy the example `.env.example` file to `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and provide your actual credentials:
        *   `GEMINI_API_KEY`: Your API key for the Google Gemini service.
        *   `SMTP_HOST`: Your SMTP server hostname (e.g., `smtp.example.com`).
        *   `SMTP_PORT`: Your SMTP server port (e.g., `587` or `465`).
        *   `SMTP_USERNAME`: Your SMTP username.
        *   `SMTP_PASSWORD`: Your SMTP password.
        *   `SMTP_SENDER_EMAIL`: The email address from which the emails will be sent.
        *   `SMTP_USE_TLS`: Set to `True` or `False`
        *   `SECRET_KEY` (Optional): A secret key for Flask sessions. A default is provided.
        *   `CSV_FILE_PATH` (Optional): Preconfigure a path for the `/view-data` test route. Defaults to `export_50.csv`.
        *   `FLASK_DEBUG` (Optional): Set to `True` for development mode. Defaults to `False`.

## Input CSV Format

*   The application expects a **CSV (Comma Separated Values)** file.
*   **Required Columns (Flexible Naming):**
    *   **Email:** The application looks for columns named "Email", "Email Address", "E-mail", "email", "Contact Email", "EmailID", or "CONTACT_EMAIL".
    *   **Company Name:** The application looks for columns named "Company Name", "Company", "Organization", "company_name", "Account Name", "CompanyName", or "COMPANY_NAME". If not found, "N/A" or a default will be used.
*   **Custom Columns:** You can include any other columns in your CSV (e.g., `Industry`, `Job Title`, `City`). These can be used as placeholders in your prompt template (e.g., `We noticed your company, {Company Name}, is a leader in the {Industry} sector located in {City}.`).

## Running the Application

1.  Ensure your `.env` file is correctly configured.
2.  Start the Flask development server:
    ```bash
    python app.py
    ```
3.  Open your web browser and navigate to `http://localhost:8080` (or the port specified in the console output).

## Using the Application

1.  **Homepage:** The main page shows the status of your Gemini and SMTP configurations.
2.  **Upload CSV:** Click "Choose File" to select your contact CSV file.
3.  **Enter Prompt:** In the "Prompt Template" text area, write your email prompt. Use curly braces `{}` to denote placeholders that correspond to column headers in your CSV file.
    *   Example: `Hi {Company Name}, I'd like to discuss opportunities in the {Industry} market.`
4.  **Process Emails:** Click "Process and Send Emails".
5.  **Results:** The application will display a summary of how many emails were successfully sent and how many failed. More detailed results for each contact will also be shown.
6.  **Logs:** Check `sent_emails.log.csv` in the application's root directory for a persistent record of all email attempts.
7.  **Statistics:** Navigate to `/stats` (e.g., `http://localhost:8080/stats`) to see a JSON response with sending statistics and recent log entries.

## Project Structure

*   `app.py`: Main Flask application file; handles routing, UI, and orchestrates the email process.
*   `email_generator.py`: Contains the logic for generating email content using the Gemini API.
*   `excel_processor.py`: Handles reading and parsing data from the uploaded CSV file. *(Note: Despite "excel" in the name, it processes CSV files).*
*   `email_sender.py`: Manages sending emails via SMTP. (This file was not explicitly reviewed but is part of the assumed structure).
*   `config.py`: Loads and provides access to configuration settings from the `.env` file.
*   `requirements.txt`: Lists Python package dependencies.
*   `.env.example`: Template for the `.env` configuration file.
*   `sent_emails.log.csv`: Log file where all email sending attempts and their outcomes are recorded.
*   `templates/index.html`: HTML template for the web interface.
*   `export_50.csv` / `export_50.xlsx`: Sample data files. Note that the application directly uses the `.csv` version.
*   `setup_ui_and_routes.sh`: A shell script. For typical local execution, running `python app.py` is sufficient. This script might have been intended for specific deployment scenarios.

## Troubleshooting

*   **"GEMINI_API_KEY is not configured"**: Ensure `GEMINI_API_KEY` is correctly set in your `.env` file and that the `.env` file is in the root directory of the project.
*   **"SMTP_HOST is not set"**: Ensure your SMTP settings (`SMTP_HOST`, `SMTP_PORT`, etc.) are correctly configured in `.env`.
*   **Emails Not Sending:**
    *   Verify SMTP credentials and server details.
    *   Check if your email provider is blocking automated emails or requires specific security settings (e.g., "less secure app access" for Gmail, though app passwords are recommended).
    *   Examine `sent_emails.log.csv` and the application's console output for error messages from the SMTP server.
*   **"No data extracted from CSV" / "Email column ... not found":**
    *   Ensure your CSV file is correctly formatted and not corrupted.
    *   Verify that your CSV has a header row with column names that match the expected patterns (see "Input CSV Format").
    *   Check for UTF-8 encoding issues.
*   **Prompt Formatting Error / Missing Key:** If you see errors like `KeyError: 'SomeColumn'`, ensure all placeholders in your prompt template (e.g., `{SomeColumn}`) exactly match a column header in your CSV file (case-sensitive).

## Important Note on `excel_processor.py`

Despite the filename `excel_processor.py`, the script is currently designed to process **CSV (Comma Separated Values)** files, not native Excel files (`.xls` or `.xlsx`). The sample `export_50.xlsx` file is not directly used by the `excel_processor.py` module; the `export_50.csv` is.
