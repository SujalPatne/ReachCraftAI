import csv
import sys # For stderr
import os # For __main__ part

def extract_data_from_csv(file_path, email_col_options=None, company_col_options=None):
    """
    Reads a CSV file and extracts data from specified columns.

    Args:
        file_path (str): The path to the CSV file.
        email_col_options (list or str): A list of possible column names for the email address.
        company_col_options (list or str): A list of possible column names for the company name.

    Returns:
        list: A list of dictionaries, where each dictionary contains
              the extracted email and company name for a row.
              Returns an empty list if required columns are not found or file fails to load.
    """
    if email_col_options is None:
        email_col_options = ["Email", "Email Address", "E-mail", "email", "Contact Email", "EmailID", "CONTACT_EMAIL"]
    if company_col_options is None:
        company_col_options = ["Company Name", "Company", "Organization", "company_name", "Account Name", "CompanyName", "COMPANY_NAME"]

    if isinstance(email_col_options, str):
        email_col_options = [email_col_options]
    if isinstance(company_col_options, str):
        company_col_options = [company_col_options]

    extracted_data = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig', newline='') as csvfile: # Added newline=''
            reader = csv.DictReader(csvfile)

            actual_email_col = None
            actual_company_col = None

            if not reader.fieldnames:
                print(f"Error: CSV file {file_path} is empty or has no header.", file=sys.stderr)
                return []

            # Normalize fieldnames: strip spaces, lower case for matching, but keep original for access
            normalized_fieldnames_map = {name.strip().lower(): name for name in reader.fieldnames}

            for option in email_col_options:
                if option.strip().lower() in normalized_fieldnames_map:
                    actual_email_col = normalized_fieldnames_map[option.strip().lower()]
                    break

            for option in company_col_options:
                if option.strip().lower() in normalized_fieldnames_map:
                    actual_company_col = normalized_fieldnames_map[option.strip().lower()]
                    break

            if not actual_email_col:
                print(f"Error: Email column (one of {email_col_options}) not found in CSV header: {reader.fieldnames}", file=sys.stderr)
                return []

            if not actual_company_col:
                print(f"Warning: Company column (one of {company_col_options}) not found in CSV header: {reader.fieldnames}. Proceeding with email only.", file=sys.stderr)

            for row_number, row in enumerate(reader, 1): # Start row_number from 1 for user messages
                email = row.get(actual_email_col)

                company_name_to_store = "N/A" # Default
                if actual_company_col: # Only try to get company name if column was identified
                    company_name_from_row = row.get(actual_company_col)
                    if company_name_from_row is not None and str(company_name_from_row).strip(): # Check if not None and not empty string after strip
                        company_name_to_store = str(company_name_from_row).strip()

                if not email or not isinstance(email, str) or not email.strip():
                    print(f"Info: Skipping row {row_number} due to missing or invalid email.", file=sys.stderr)
                    continue

                data_entry = {
                    "Email": email.strip(),
                    "Company Name": company_name_to_store
                }
                extracted_data.append(data_entry)

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error reading CSV file {file_path}: {e}", file=sys.stderr)
        return []

    return extracted_data

if __name__ == "__main__":
    # This test part won't run in the subtask if pip fails earlier,
    # but it's here for completeness if the script is run manually later.
    file_to_test = "export_50.csv"

    # Check if the test file exists
    if not os.path.exists(file_to_test):
        print(f"Error: Test file '{file_to_test}' does not exist in the current directory ({os.getcwd()}).", file=sys.stderr)
        # Attempt to list files in current directory for debugging
        try:
            print(f"Files in current directory: {os.listdir('.')}", file=sys.stderr)
        except Exception as e_ls:
            print(f"Could not list files in current directory: {e_ls}", file=sys.stderr)
        sys.exit(1) # Exit if test file is missing

    print(f"Attempting to process {file_to_test} using excel_processor.py (CSV version)...")
    data = extract_data_from_csv(file_to_test)

    if data:
        print(f"Successfully extracted {len(data)} entries (first 5 shown):")
        for i, entry in enumerate(data):
            if i < 5:
                print(entry)
            elif i == 5:
                print("...")
                break
    else:
        print(f"No data extracted or an error occurred while processing {file_to_test}.")
