import google.generativeai as genai
import os
import sqlite3
import re # Import regular expressions for cleaning filename

# Import or define your API key handling (e.g., from config.py)
import config

def create_study_guide_md(topic_name: str,
                          question_txt_filepath: str,
                          db_filepath: str = 'database.db',
                          output_dir: str = '.',
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
        api_key = config.api_key # Load your API key
        genai.configure(api_key=api_key)
        # print(f"Configured Gemini API with model: {model_name}")
        # --- Placeholder for API Key Configuration ---
        print("Placeholder: Configure Gemini API here.")


        # --- 2. Validate Inputs & Create Output Directory ---
        if not os.path.exists(db_filepath):
            print(f"Error: Database file not found at '{db_filepath}'")
            return None
        if not os.path.exists(question_txt_filepath):
            print(f"Error: Question text file not found at '{question_txt_filepath}'")
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
        question_file_normalized = os.path.normpath(question_txt_filepath) # Normalize for comparison
        # Query to find linked files
        cursor.execute("""
            SELECT DISTINCT s.filepath, s.filename
            FROM Sources s
            LEFT JOIN Topic_Source_Locations tsl ON s.source_id = tsl.source_id AND tsl.topic_id = ?
            LEFT JOIN Subtopic_Source_Locations ssl ON s.source_id = ssl.source_id
            LEFT JOIN Subtopics sub ON ssl.subtopic_id = sub.subtopic_id AND sub.topic_id = ?
            LEFT JOIN Mistakes m ON s.source_id = m.source_id AND (m.topic_id = ? OR m.subtopic_id IN (SELECT subtopic_id FROM Subtopics WHERE topic_id = ?))
            WHERE tsl.topic_id = ? OR sub.topic_id = ? OR m.topic_id = ?
        """, (topic_id, topic_id, topic_id, topic_id, topic_id, topic_id, topic_id))

        # <<< MODIFICATION START >>>
        for row in cursor.fetchall():
            fpath = row[0] # Get the value from the 'filepath' column
            # fname = row[1] # Optional: Get filename if needed for display name

            full_path = None # Initialize full_path for this iteration
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
        # <<< MODIFICATION END >>>

        print(f"Found {len(relevant_files_from_db)} relevant file(s) in DB for topic '{topic_name}' (excluding question file if listed).")


        # --- 5. Prepare Final List of Files to Upload ---
        files_to_upload_paths = set()
        # Add DB files (check existence using the path directly from 'filepath' column)
        for f_path in relevant_files_from_db:
             if os.path.exists(f_path):
                 files_to_upload_paths.add(f_path)
                 print(f"  - Adding DB file: '{f_path}'")
             else:
                 print(f"  - Warning: DB file not found on disk, skipping: '{f_path}'")
        # Add the question file (already checked existence)
        files_to_upload_paths.add(question_file_normalized)
        print(f"  - Adding Question file: '{question_file_normalized}'")

        if not files_to_upload_paths:
             print(f"Error: No valid files to upload for topic '{topic_name}'. Cannot generate guide.")
             if conn: conn.close() # Ensure connection is closed before returning
             return None


        # --- 6. Upload Files to Gemini ---
        gemini_files = []
        file_metadata_for_prompt = []
        print("\nUploading files to Gemini:")
        for file_path in files_to_upload_paths:
            print(f"  Uploading '{file_path}'...")
            try:
                # Use os.path.basename to get the display name from the full path
                file_basename = os.path.basename(file_path)
                file_obj = genai.upload_file(path=file_path, display_name=file_basename)
                gemini_files.append(file_obj)
                uploaded_files_info.append({'name': file_obj.name, 'path': file_path})
                # Store the basename derived from the full path for the prompt
                file_metadata_for_prompt.append({'filename': file_basename, 'uri': file_obj.uri})
                print(f"    Uploaded successfully: {file_obj.uri} (Filename: {file_basename})")
            except Exception as upload_err:
                print(f"    Warning: Failed to upload file '{file_path}'. Error: {upload_err}. Skipping this file.")

        if not gemini_files:
             print("Error: Failed to upload any files to Gemini. Cannot generate guide.")
             if conn: conn.close() # Ensure connection is closed before returning
             return None


        # --- 7. Construct Gemini Prompt ---
        question_file_basename = os.path.basename(question_txt_filepath)
        # Use the filenames derived in step 6 for the prompt list
        file_list_str = "\n".join([f"- {meta['filename']}" for meta in file_metadata_for_prompt])

        prompt = f"""
        Generate a comprehensive study guide in **Markdown format** for the topic: "{topic_name}".

        You have been provided with the following files:
        {file_list_str}

        One of these files, specifically "{question_file_basename}", contains questions related to the topic. The other files contain relevant context like lecture notes, examples, etc.

        Your task is to:
        1. Synthesize the information from ALL provided files.
        2. Explain the core concepts related to "{topic_name}" using the context files.
        3. Analyze the questions in "{question_file_basename}" and discuss common mistakes, approaches, or important points related to answering them, using the context files for support.
        4. Provide clear examples or illustrations of the concepts, drawing from the context files.
        5. Offer tips or strategies for mastering the topic.
        6. **Crucially, for any information, concept, example, mistake, or question analysis you mention, you MUST cite the source file(s) where it originates using the format [Filename] or [Filename, Page X] or [Filename, Location Y] if page number or location details are available in the context.** Base your citations ONLY on the provided filenames listed above (use the base filenames like 'lecture1.pdf', not the full paths).

        Structure the guide logically using **Markdown formatting** (headings, lists, bold text, etc.). Ensure the entire output is valid Markdown.
        """
        print("\nGenerating Markdown study guide...")


        # --- 8. Call Gemini API ---
        model = genai.GenerativeModel(model_name=model_name)
        # Increase timeout if needed for complex generation
        # request_options = genai.types.RequestOptions(timeout=600) # 10 minutes
        response = model.generate_content(contents=[prompt] + gemini_files,
                                          # request_options=request_options
                                          )

        # --- 9. Process Response and Save Markdown ---
        if not response.parts:
             print("Warning: Received empty response from API. Check prompt feedback.")
             study_guide_markdown = "Error: Received no content from the API."
             try: print(f"Prompt Feedback: {response.prompt_feedback}")
             except Exception: pass
        else:
            study_guide_markdown = response.text
            print("Study guide Markdown generated successfully.")

            # Clean topic name for filename
            safe_topic_name = re.sub(r'[^\w\-_\. ]', '_', topic_name) # Replace invalid chars
            output_filename = f"Study_Guide_{safe_topic_name}.md"
            output_filepath = os.path.join(output_dir, output_filename)

            try:
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    f.write(study_guide_markdown)
                print(f"Successfully saved Markdown study guide to: {output_filepath}")
            except IOError as e:
                print(f"Error: Failed to save study guide to file '{output_filepath}'. Error: {e}")
                output_filepath = None # Indicate failure to save


        return output_filepath # Return path if saved, None otherwise

    except sqlite3.Error as db_err:
        print(f"Error: Database error occurred - {db_err}")
        return None
    except ValueError as val_err: # Catch configuration errors
         print(f"Error: Configuration error - {val_err}")
         return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
            try: print(f"Prompt Feedback: {response.prompt_feedback}")
            except Exception: pass
        if 'response' in locals() and hasattr(response, 'candidates') and response.candidates:
            try:
                 print(f"Candidate Finish Reason: {response.candidates[0].finish_reason}")
                 print(f"Candidate Safety Ratings: {response.candidates[0].safety_ratings}")
            except Exception: pass
        return None

    finally:
        # --- 10. Clean Up ---
        if conn:
            conn.close()
            print("Database connection closed.")

        if uploaded_files_info:
            print("\nCleaning up uploaded files on Google Cloud...")
            # for file_info in uploaded_files_info:
            #     try:
            #         print(f"  Deleting uploaded file: {file_info['name']} (from path: {file_info['path']})")
            #         # genai.delete_file(file_info['name']) # Uncomment when API key is configured
            #     except Exception as delete_err:
            #         print(f"    Warning: Error deleting file {file_info['name']}: {delete_err}")
            # --- Placeholder for File Deletion ---
            print("Placeholder: Delete uploaded files here using their internal names.")
        print("-" * 30)