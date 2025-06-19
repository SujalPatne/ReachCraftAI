import os
try:
    import google.generativeai as genai
    print("Successfully imported google.generativeai.")
except ImportError:
    print("Warning: google-generativeai library not found. Email generation will not work.")
    print("Please install it if running locally: pip install google-generativeai")
    genai = None # Placeholder

# Attempt to import settings from config.py
# This assumes config.py is in the same directory or accessible via PYTHONPATH
try:
    from config import settings
    print("Successfully imported settings from config.")
except ImportError:
    print("Error: Could not import settings from config.py. Ensure config.py exists and is accessible.")
    # Define a dummy settings object for the script to be syntactically valid if config is missing
    class DummySettings:
        GEMINI_API_KEY = None
    settings = DummySettings()


def generate_email_content(company_data, user_prompt):
    """
    Generates email content using the Gemini API.

    Args:
        company_data (dict): A dictionary containing company-specific data.
        user_prompt (str): The user-defined prompt or template for the email.

    Returns:
        str: The generated email content, or an error message if generation fails.
    """
    if not genai:
        return "Error: google-generativeai library is not installed or loaded."

    if not settings.GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY is not configured in settings."

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)

        model = genai.GenerativeModel('gemini-1.0-pro')

        prompt_for_api = user_prompt.format(**company_data) # Basic placeholder replacement

        full_prompt = f"""
        Generate a professional and personalized email based on the following information and instructions:

        Company Information:
        - Company Name: {company_data.get("Company Name", "N/A")}
        - Other Details: {company_data}

        User Instructions:
        {prompt_for_api}

        Please generate only the body of the email.
        """

        print(f"Debug: Sending prompt to Gemini API: {full_prompt[:150]}...") # Log snippet of prompt
        response = model.generate_content(full_prompt)

        if response.parts:
            print("Debug: Received response with parts from Gemini API.")
            return response.text
        else:
            block_reason = "Unknown"
            safety_ratings_str = "N/A"
            if response.prompt_feedback:
                block_reason = response.prompt_feedback.block_reason
                safety_ratings_str = str(response.prompt_feedback.safety_ratings)
            else: # If prompt_feedback itself is None
                 print("Debug: No prompt_feedback in response.")


            print(f"Error: Failed to generate content. Block Reason: {block_reason}. Safety Ratings: {safety_ratings_str}")
            return f"Error: Failed to generate content. Block Reason: {block_reason}. Safety Ratings: {safety_ratings_str}"

    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        return f"Error generating email content: {str(e)}"

if __name__ == '__main__': # Corrected: added quotes around '__main__'
    print("--- Email Generator Test ---")

    if not genai:
        print("Skipping test: google-generativeai library not available.")
    elif not settings.GEMINI_API_KEY:
        print("Skipping test: GEMINI_API_KEY not set in config settings.")
    else:
        print(f"Attempting to use Gemini API with key starting with: {settings.GEMINI_API_KEY[:5] if settings.GEMINI_API_KEY else 'None'}...")
        sample_company = {"Company Name": "Innovate Corp", "Industry": "Tech"}
        sample_prompt = "Write a brief introductory email to {Company Name}, highlighting our innovative solutions for the {Industry} sector."

        print(f"Test Company Data: {sample_company}")
        print(f"Test User Prompt: {sample_prompt}")

        email_body = generate_email_content(sample_company, sample_prompt)

        print("\n--- Generated Email Body ---")
        print(email_body)
        print("--------------------------")
