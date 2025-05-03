import google.generativeai as genai
import os
import json

# --- Import the database creation function ---
# Make sure create_database.py is in the same directory or your Python path
from create_database import create_database_from_json


# --- Main Processing Function ---
def process_pdf_to_db(pdf_filepath, db_filepath,GEMINI_PROMPT):
    """
    Analyzes a PDF using Gemini, saves the JSON response, and populates a database.
    Requires the Google API key to be passed.

    Args:
        pdf_filepath (str): Path to the input PDF file.
        db_filepath (str): Path to the SQLite database file to create/update.
        api_key (str): Your Google API Key for Generative AI.

    Returns:
        bool: True if processing and database update were successful, False otherwise.
    """
    # --- Configure API within the function ---
    api_key='AIzaSyBCnOUfUWbVD0VdJBc62qwFH01McBQVN_o'
    if not api_key:
        print("ERROR: Google API Key is required but was not provided.")
        return False
    try:
        genai.configure(api_key=api_key)
        print("Google GenAI configured successfully within function.")
    except Exception as e:
        print(f"ERROR configuring Google GenAI: {e}")
        return False # Exit if configuration fails

    # --- Internal Fixed Parameters ---
    filename_py = 'create_database.py' # Assumed location of the script for context/upload
    output_filename = 'response_output.json' # Intermediate JSON output path
    fallback_filename = 'response_raw.txt' # Fallback path for invalid JSON
    model_name = "gemini-2.5-flash-preview-04-17" # Model to use



    # --- Function Logic ---
    file1 = None # PDF file object
    file2 = None # Python script file object
    json_successfully_created = False # Flag to track JSON file readiness

    try:
        print("-" * 30)
        print(f"Starting processing for PDF: '{pdf_filepath}'")
        print(f"Target database: '{db_filepath}'")

        # --- File Uploads ---
        print(f"Uploading PDF: {pdf_filepath}...")
        file1 = genai.upload_file(path=pdf_filepath) # Use parameter
        print(f"Uploaded PDF file URI: {file1.uri}")

        # Check if the python script file exists before trying to upload
        if not os.path.exists(filename_py):
             print(f"ERROR: Required Python script '{filename_py}' not found in the current directory.")
             if file1: genai.delete_file(file1.name) # Clean up already uploaded file
             return False # Cannot proceed without the script context

        print(f"Uploading Python script context: {filename_py}...")
        file2 = genai.upload_file(path=filename_py)
        print(f"Uploaded Python file URI: {file2.uri}")

        # --- Call Gemini API ---
        model = genai.GenerativeModel(model_name=model_name)
        print(f"Generating content using model '{model_name}'...")
        response = model.generate_content(
            contents=[GEMINI_PROMPT, file1, file2]
        )
        print("Response received from API.")
        raw_response_text = response.text

        # --- Clean/Parse/Save Response ---
        try:
            print("Attempting to clean and parse API response as JSON...")
            cleaned_text = raw_response_text.strip()
            # Remove ```json header if present
            if cleaned_text.lower().startswith("```json"):
                first_line_end = cleaned_text.find('\n')
                if first_line_end != -1: cleaned_text = cleaned_text[first_line_end:].strip()
                else: cleaned_text = cleaned_text[len("```json"):].strip()
                print("Removed leading '```json' marker.")
            # Remove ``` footer if present
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-len("```")].strip()
                print("Removed trailing '```' marker.")

            response_data = json.loads(cleaned_text)
            print(f"Successfully parsed JSON.")

            print(f"Saving valid JSON response to '{output_filename}'...")
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=4, ensure_ascii=False)
            print(f"Successfully saved JSON to '{output_filename}'.")
            json_successfully_created = True # Set flag

        except json.JSONDecodeError:
            print("ERROR: Failed to decode API response as JSON even after cleaning.")
            print(f"Saving original raw response text to fallback file: '{fallback_filename}'")
            with open(fallback_filename, 'w', encoding='utf-8') as f:
                f.write(raw_response_text)
            json_successfully_created = False
        except Exception as e:
            print(f"ERROR during JSON cleaning/saving: {e}")
            json_successfully_created = False
        # --- End cleaning/saving ---

        # --- Call Database Function (Conditional) ---
        if json_successfully_created:
            print(f"\nAttempting to update database '{db_filepath}' from '{output_filename}'...")
            try:
                # **** THE ACTUAL CALL TO YOUR DATABASE SCRIPT'S FUNCTION ****
                create_database_from_json(output_filename, db_filepath) # Pass parameters
                # *************************************************************
                print(f"Successfully called create_database_from_json.")
                return True # Overall success
            except Exception as db_e:
                print(f"ERROR during database update call: {db_e}")
                return False # DB step failed
        else:
            print("\nSkipping database update because JSON generation failed.")
            return False # JSON step failed

    except FileNotFoundError as e:
        print(f"ERROR: Input file not found - {e}. Please check the path: '{pdf_filepath}'")
        return False
    except Exception as e:
        print(f"ERROR during API call or file upload: {e}")
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
            print(f"Prompt Feedback: {response.prompt_feedback}")
        if 'response' in locals() and hasattr(response, 'candidates') and response.candidates:
            print(f"Finish Reason: {response.candidates[0].finish_reason}")
            print(f"Safety Ratings: {response.candidates[0].safety_ratings}")
        return False

    finally:
        # --- Clean up uploaded Google Cloud files ---
        files_to_delete = [f for f in [file1, file2] if f]
        if files_to_delete:
             print("\nCleaning up uploaded files on Google Cloud...")
        for f in files_to_delete:
             try:
                 print(f"Deleting uploaded file: {f.name}")
                 genai.delete_file(f.name)
             except Exception as e:
                 print(f"Warning: Error deleting file {f.name}: {e}")
        print("-" * 30)

# --- Example Usage (How to call the function) ---
if __name__ == "__main__":
    print("="*40)
    print("Running Example Usage")
    print("="*40)

    # --- Get API Key (Recommended: Environment Variable) ---
    # Load the API key from an environment variable for security
    my_api_key = os.environ.get("GOOGLE_API_KEY")

    # --- OR: Hardcode for testing (Less Secure) ---
    # Replace "YOUR_GOOGLE_API_KEY_HERE" with your actual key if not using environment variables
    # my_api_key = "YOUR_GOOGLE_API_KEY_HERE"

    if not my_api_key:
        print("ERROR: GOOGLE_API_KEY environment variable not set.")
        print("Please set the environment variable or hardcode the key in the script (less recommended).")
    else:
        # Define the input PDF and output database paths for the example
        pdf_to_process = 'data/Automation_P02_SensorConcepts.pdf'
        database_file = 'automation_concepts.db' # Example database name

        # Basic check if the example PDF file exists
        if os.path.exists(pdf_to_process):
            # Call the main processing function, passing the API key
            success = process_pdf_to_db(
                pdf_filepath=pdf_to_process,
                db_filepath=database_file,
                api_key=my_api_key # Pass the key here
            )

            if success:
                print("\nProcessing completed successfully.")
                print(f"Database '{database_file}' should be updated.")
            else:
                print("\nProcessing failed.")
                print(f"Check logs above for errors. Database '{database_file}' might be incomplete or not updated.")
        else:
             print(f"ERROR: Example PDF file '{pdf_to_process}' not found.")
             print("Please ensure the file exists at the specified path to run the example.")

    print("="*40)
    print("Example Usage Finished")
    print("="*40)