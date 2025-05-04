import google.generativeai as genai
import os
import sqlite3
import re # Import regular expressions for cleaning filename

# Import or define your API key handling (e.g., from config.py)
# Ensure config.py exists and contains your API key
try:
    import config
except ImportError:
    print("Error: config.py not found. Please ensure it exists and contains your API key.")
    # Handle the error appropriately, maybe exit or raise an exception
    # For now, we'll set api_key to None and let the genai configure call fail later
    config = type('obj', (object,), {'api_key': None})()


def create_study_guide_md(topic_name: str,
                          question_txt_filepath: str,
                          db_filepath: str = 'database.db',
                          output_dir: str = 'study_guides',
                          model_name: str = "gemini-2.5-flash-preview-04-17") -> str | None:
    """
    Generates a Markdown study guide for a topic using Gemini.

    Finds relevant content files for the topic in the database (assuming the
    'filepath' column stores the full path), combines them with the provided
    question text file, asks Gemini to generate a cited Markdown study guide,
    and saves it to a file.

    Args:
        topic_name (str): The name of the topic.
        question_txt_filepath (str): The path to the text file containing questions.
        db_filepath (str): Path to the SQLite database file.
        output_dir (str): Directory where the generated Markdown file will be saved.
        model_name (str): The Gemini model to use.

    Returns:
        str | None: The full path to the saved Markdown file if successful,
                    otherwise None.
    """
    conn = None
    uploaded_files_info = []
    output_filepath = None # Path to the saved markdown file

    try:
        # --- 1. Configure Gemini API ---
        api_key = config.api_key # Load your API key from config.py
        if not api_key:
             print("Error: Gemini API Key not found in config.py or config object.")
             return None
        genai.configure(api_key=api_key)
        print(f"Configured Gemini API with model: {model_name}")


        # --- 2. Validate Inputs & Create Output Directory ---
        if not os.path.exists(db_filepath):
            print(f"Error: Database file not found at '{db_filepath}'")
            return None
        # Normalize the question file path *before* checking existence
        question_file_normalized = os.path.normpath(question_txt_filepath)
        if not os.path.exists(question_file_normalized):
            print(f"Error: Question text file not found at '{question_file_normalized}'")
            return None
        os.makedirs(output_dir, exist_ok=True) # Create output dir if it doesn't exist


        # --- 3. Connect to Database & Find Topic ID ---
        conn = sqlite3.connect(db_filepath)
        cursor = conn.cursor()
        print(f"Connected to database: {db_filepath}")
        cursor.execute("SELECT topic_id FROM Topics WHERE topic_name = ?", (topic_name,))
        topic_result = cursor.fetchone()
        if not topic_result:
            print(f"Error: Topic '{topic_name}' not found in the database.")
            conn.close()
            return None
        topic_id = topic_result[0]
        print(f"Found Topic ID for '{topic_name}': {topic_id}")


        # --- 4. Find Relevant Files from DB (Excluding the question file itself if listed) ---
        relevant_files_from_db = set()
        # Query to find linked files (using filepath directly)
        cursor.execute("""
            SELECT DISTINCT s.filepath, s.filename
            FROM Sources s
            LEFT JOIN Topic_Source_Locations tsl ON s.source_id = tsl.source_id AND tsl.topic_id = ?
            LEFT JOIN Subtopic_Source_Locations ssl ON s.source_id = ssl.source_id
            LEFT JOIN Subtopics sub ON ssl.subtopic_id = sub.subtopic_id AND sub.topic_id = ?
            LEFT JOIN Mistakes m ON s.source_id = m.source_id AND (m.topic_id = ? OR m.subtopic_id IN (SELECT subtopic_id FROM Subtopics WHERE topic_id = ?))
            LEFT JOIN Good_Answers ga ON s.source_id = ga.source_id AND (ga.topic_id = ? OR ga.subtopic_id IN (SELECT subtopic_id FROM Subtopics WHERE topic_id = ?))
            WHERE tsl.topic_id = ? OR sub.topic_id = ? OR m.topic_id = ? OR ga.topic_id = ?
        """, (topic_id, topic_id, topic_id, topic_id, topic_id, topic_id, topic_id, topic_id, topic_id, topic_id)) # Ensure all placeholders are filled

        for row in cursor.fetchall():
            fpath = row[0] # Get the value from the 'filepath' column
            if fpath: # Check if filepath column value is not None or empty
                # Assume fpath directly contains the full path including the filename
                full_path = os.path.normpath(fpath)

                # Add if it's not the explicitly provided question file
                if full_path != question_file_normalized:
                    relevant_files_from_db.add(full_path)
                # else: # Implicitly skip if it IS the question file
                #    print(f"  (Info: Skipping '{full_path}' as it matches the question file)") # Optional info log
            else:
                # Handle cases where filepath might be missing in the DB
                print(f"  Warning: Found database entry with missing filepath for topic '{topic_name}'. Skipping row.")
                continue # Skip to the next row in the loop

        print(f"Found {len(relevant_files_from_db)} relevant file(s) in DB for topic '{topic_name}' (excluding question file if listed).")


        # --- 5. Prepare Final List of Files to Upload (Maintain order) ---
        # Use a list to maintain order for prompt generation
        files_to_upload_paths_ordered = []

        # Add DB files first (order within this group might vary based on set iteration)
        # Check existence using the path directly from 'filepath' column
        for f_path in sorted(list(relevant_files_from_db)): # Sort for consistency, though not strictly required by user
             if os.path.exists(f_path):
                 if f_path not in files_to_upload_paths_ordered: # Avoid duplicates if somehow present
                     files_to_upload_paths_ordered.append(f_path)
                     print(f"  - Adding DB file: '{f_path}'")
             else:
                 print(f"  - Warning: DB file not found on disk, skipping: '{f_path}'")

        # Add the question file last (or first, consistently)
        # Let's add it last to easily reference "other files" in the prompt
        if question_file_normalized not in files_to_upload_paths_ordered: # Ensure it's not already added
            files_to_upload_paths_ordered.append(question_file_normalized)
            print(f"  - Adding Question file: '{question_file_normalized}'")

        if not files_to_upload_paths_ordered:
             print(f"Error: No valid files to process for topic '{topic_name}'. Cannot generate guide.")
             if conn: conn.close() # Ensure connection is closed before returning
             return None


        # --- 6. Upload Files to Gemini ---
        gemini_files = [] # List to hold file objects for the API call
        file_metadata_for_prompt = [] # List to hold info for the prompt text
        print("\nUploading files to Gemini:")
        for file_path in files_to_upload_paths_ordered: # Iterate in defined order
            print(f"  Uploading '{file_path}'...")
            try:
                # Use os.path.basename to get the display name from the full path
                file_basename = os.path.basename(file_path)
                file_obj = genai.upload_file(path=file_path, display_name=file_basename)
                gemini_files.append(file_obj) # Add file object for API
                uploaded_files_info.append({'name': file_obj.name, 'path': file_path}) # For cleanup
                # Store the basename derived from the full path for the prompt list
                file_metadata_for_prompt.append({'filename': file_basename, 'uri': file_obj.uri})
                print(f"    Uploaded successfully: {file_obj.uri} (Filename: {file_basename})")
            except Exception as upload_err:
                print(f"    Warning: Failed to upload file '{file_path}'. Error: {upload_err}. Skipping this file.")
                # Crucially, don't add metadata for failed uploads to file_metadata_for_prompt

        if not gemini_files:
             print("Error: Failed to upload any files to Gemini. Cannot generate guide.")
             if conn: conn.close() # Ensure connection is closed before returning
             # Clean up any files that *were* successfully uploaded before this check failed
             # (Cleanup logic is in the finally block, which will run)
             return None


        # --- 7. Construct Gemini Prompt ---
        # <<< MODIFICATION START >>>
        question_file_basename = os.path.basename(question_file_normalized)
        # Use the filenames derived in step 6 (which respected the order)
        # Ensure only metadata from successfully uploaded files is included
        file_list_str = "\n".join([f"- {meta['filename']}" for meta in file_metadata_for_prompt])

        # Updated prompt incorporating user requests
        prompt = f"""
        Generate a comprehensive study guide in **Markdown format** for the topic: "{topic_name}".

        You have been provided with the following files, **in this order**:
        {file_list_str}

        One of these files, specifically "{question_file_basename}", contains questions for the study guide.

        Your task is to:
        1.  **Use the files *other than* "{question_file_basename}" as the primary source of information and context.** Explain the core concepts related to "{topic_name}" using these context files. Do NOT use "{question_file_basename}" as a source for explanations or definitions.
        2.  Analyze the questions found *only* in "{question_file_basename}". Discuss common mistakes, approaches, or important points related to answering these specific questions, using the context files (i.e., all files *except* "{question_file_basename}") for support and explanation.
        3.  Provide clear examples or illustrations of the concepts, drawing primarily from the context files (all files *except* "{question_file_basename}").
        4.  Offer tips or strategies for mastering the topic based on the information in the context files (all files *except* "{question_file_basename}").
        5.  **Crucially, for any information, concept, example, mistake, or question analysis you mention, you MUST cite the source file(s) where it originates using the format [Filename] or [Filename, Page X] or [Filename, Location Y] if page number or location details are available in the context.** Base your citations ONLY on the provided filenames listed above (use the base filenames like 'lecture1.pdf', not the full paths). Ensure citations accurately reflect the source used for that specific piece of information. **Do not cite "{question_file_basename}" for conceptual explanations, only when referring to the questions themselves.**
        6.  Focus the guide on understanding and answering the questions from "{question_file_basename}", supported by the theory and examples from the other files. Avoid simply summarizing all documents fully; prioritize relevance to the questions in "{question_file_basename}".

        Structure the guide logically using **Markdown formatting** (headings, lists, bold text, etc.). Ensure the entire output is valid Markdown.
        """
        # <<< MODIFICATION END >>>

        print("\nConstructed Prompt:\n" + "="*20 + f"\n{prompt}\n" + "="*20) # Print the prompt for debugging

        print("\nGenerating Markdown study guide (this may take some time)...")


        # --- 8. Call Gemini API ---
        model = genai.GenerativeModel(model_name=model_name)
        # Increase timeout if needed for complex generation
        request_options = genai.types.RequestOptions(timeout=600) # 10 minutes
        try:
            response = model.generate_content(contents=[prompt] + gemini_files, # Pass the prompt and the uploaded file objects
                                              request_options=request_options
                                              )
        except Exception as api_err:
            print(f"Error calling Gemini API: {api_err}")
            # Attempt to get feedback even on error
            if 'response' in locals() and hasattr(response, 'prompt_feedback'):
                try: print(f"Prompt Feedback (on error): {response.prompt_feedback}")
                except Exception: pass
            return None # Exit after API error

        # --- 9. Process Response and Save Markdown ---
        study_guide_markdown = "" # Initialize
        try:
            if not response.parts:
                 print("Warning: Received empty response parts from API. Check prompt feedback.")
                 study_guide_markdown = f"Error: Received no content parts from the API for topic '{topic_name}'."
                 # Try to print feedback if available
                 if hasattr(response, 'prompt_feedback'): print(f"Prompt Feedback: {response.prompt_feedback}")
            else:
                # Assuming the response text is in the first part if parts exist
                study_guide_markdown = response.text
                print("Study guide Markdown generated successfully.")

        except Exception as resp_err:
             print(f"Error processing API response: {resp_err}")
             study_guide_markdown = f"Error processing API response for topic '{topic_name}'. Details: {resp_err}"
             # Try to print feedback if available
             if hasattr(response, 'prompt_feedback'): print(f"Prompt Feedback: {response.prompt_feedback}")


        # Clean topic name for filename regardless of API success, to save error messages too
        safe_topic_name = re.sub(r'[^\w\-_\. ]', '_', topic_name) # Replace invalid chars
        output_filename = f"Study_Guide_{safe_topic_name}.md"
        output_filepath = os.path.join(output_dir, output_filename)

        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(study_guide_markdown) # Write content or error message
            print(f"Successfully saved output Markdown to: {output_filepath}")
        except IOError as e:
            print(f"Error: Failed to save output Markdown to file '{output_filepath}'. Error: {e}")
            output_filepath = None # Indicate failure to save

        # Check finish reason if response object exists
        if 'response' in locals() and hasattr(response, 'candidates') and response.candidates:
            finish_reason = response.candidates[0].finish_reason
            print(f"Generation Finish Reason: {finish_reason}")
            if finish_reason not in ["STOP", "MAX_TOKENS"]: # Check for problematic reasons
                 print(f"Warning: Finish reason was '{finish_reason}'. Check output quality and safety ratings.")
                 if hasattr(response.candidates[0], 'safety_ratings'):
                     print(f"Safety Ratings: {response.candidates[0].safety_ratings}")


        return output_filepath # Return path if saved, None otherwise

    except sqlite3.Error as db_err:
        print(f"Error: Database error occurred - {db_err}")
        return None
    except ValueError as val_err: # Catch configuration or validation errors
         print(f"Error: Value or Configuration error - {val_err}")
         return None
    except Exception as e:
        print(f"An unexpected error occurred in create_study_guide_md: {e}")
        # Include prompt feedback if available and an API call was attempted
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
            try: print(f"Prompt Feedback (on unexpected error): {response.prompt_feedback}")
            except Exception: pass
        return None

    finally:
        # --- 10. Clean Up ---
        if conn:
            conn.close()
            print("Database connection closed.")

        if uploaded_files_info:
            print("\nCleaning up uploaded files on Google Cloud...")
            for file_info in uploaded_files_info:
                try:
                    print(f"  Deleting uploaded file: {file_info['name']} (from path: {file_info['path']})")
                    genai.delete_file(file_info['name']) # Use the internal API name for deletion
                except Exception as delete_err:
                    # Log warning but continue cleanup
                    print(f"    Warning: Error deleting file {file_info['name']}: {delete_err}")
        print("-" * 30)

