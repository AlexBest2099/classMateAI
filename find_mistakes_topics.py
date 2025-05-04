import sqlite3
import os
import sys

# --- Configuration ---
DEFAULT_DB_FILE = 'database.db'

def get_topics_with_mistakes(db_filepath: str = DEFAULT_DB_FILE) -> list[str] | None:
    """
    Finds all unique topic names that have at least one mistake associated with them.
    Suitable for populating a UI list.

    Args:
        db_filepath: Path to the SQLite database file.

    Returns:
        A list of unique topic names (strings) that have mistakes,
        or None if an error occurs.
        Returns an empty list if the tables exist but no mistakes are recorded.
    """
    # (Implementation remains the same as the previous version)
    if not os.path.exists(db_filepath):
        print(f"Error: Database file not found at '{db_filepath}'", file=sys.stderr)
        return None

    topics_with_mistakes = []
    try:
        with sqlite3.connect(db_filepath) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('Mistakes', 'Topics');")
            tables_found = {row['name'] for row in cursor.fetchall()}
            if 'Mistakes' not in tables_found or 'Topics' not in tables_found:
                print("Error: Required tables ('Mistakes', 'Topics') not found.", file=sys.stderr)
                return None
            query = """
                SELECT DISTINCT T.topic_name
                FROM Mistakes M
                JOIN Topics T ON M.topic_id = T.topic_id
                ORDER BY T.topic_name;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            topics_with_mistakes = [row['topic_name'] for row in rows]
    except sqlite3.Error as e:
        print(f"Error: DB query failed. SQLite error: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: Unexpected error during DB access: {e}", file=sys.stderr)
        return None
    return topics_with_mistakes





def export_questions_for_topic_to_txt(
    topic_name: str,
    output_filepath: str, # Specify the exact path for the output .txt file
    db_filepath: str = DEFAULT_DB_FILE
) -> bool:
    """
    Retrieves question formulations for a specific topic and writes them,
    numbered, to a text file. Adds a header line indicating the output filename.

    Args:
        topic_name: The name of the topic to filter by.
        output_filepath: The full path where the text file should be saved.
        db_filepath: Path to the SQLite database file.

    Returns:
        True if the questions were successfully exported to the file,
        False otherwise (e.g., topic not found, DB error, file writing error).
    """
    if not os.path.exists(db_filepath):
        print(f"Error: Database file not found at '{db_filepath}'", file=sys.stderr)
        return False

    formulations_data = []
    try:
        with sqlite3.connect(db_filepath) as conn:
            conn.row_factory = sqlite3.Row # Use Row factory
            cursor = conn.cursor()

            # Check tables (Keep Sources check in case needed later, but not strictly required for this version)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('Mistakes', 'Topics', 'Sources');")
            tables_found = {row['name'] for row in cursor.fetchall()}
            if not {'Mistakes', 'Topics'}.issubset(tables_found): # Only strictly need Mistakes & Topics now
                missing = {'Mistakes', 'Topics'} - tables_found
                print(f"Error: Required tables ({', '.join(missing)}) not found.", file=sys.stderr)
                return False

            # Find topic_id
            cursor.execute("SELECT topic_id FROM Topics WHERE topic_name = ?", (topic_name,))
            topic_result = cursor.fetchone()
            if not topic_result:
                print(f"Info: Topic '{topic_name}' not found.", file=sys.stderr)
                return False
            topic_id = topic_result['topic_id']

            # Check column exists
            cursor.execute("PRAGMA table_info(Mistakes)")
            columns = [col['name'] for col in cursor.fetchall()]
            if 'problem_formulation' not in columns:
                 print(f"Error: 'problem_formulation' column not found.", file=sys.stderr)
                 return False

            # --- ORIGINAL QUERY: Only need problem_formulation ---
            query = "SELECT M.problem_formulation FROM Mistakes M WHERE M.topic_id = ?;"
            cursor.execute(query, (topic_id,))
            formulations_data = cursor.fetchall() # List of Row objects

    except sqlite3.Error as e:
        print(f"Error: DB query failed. SQLite error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: Unexpected error during DB access: {e}", file=sys.stderr)
        return False

    # --- MODIFIED FILE WRITING ---
    question_number = 0
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_filepath)
        if output_dir:
             os.makedirs(output_dir, exist_ok=True)

        with open(output_filepath, 'w', encoding='utf-8') as f:
            # --- ADDED HEADER LINE ---
            base_filename = os.path.basename(output_filepath)
            f.write(f"Filename: {base_filename}\n\n") # Write header + blank line
            # -------------------------

            for row in formulations_data:
                formulation = row['problem_formulation']
                # Only write non-empty formulations
                if formulation:
                    question_number += 1
                    # Replace potential literal '\n' with actual newlines
                    cleaned_formulation = str(formulation).replace('\\n', '\n')
                    # Original writing format for the question itself
                    f.write(f"{question_number}: {cleaned_formulation}\n\n") # Add extra newline

        if question_number > 0:
            print(f"Successfully exported {question_number} question(s) for topic '{topic_name}' to '{output_filepath}'.")
        else:
            # File is still created with header even if no questions found
            print(f"No questions with formulations found for topic '{topic_name}'. Output file '{output_filepath}' created with header only.")
        return True

    except IOError as e:
        print(f"Error: Failed to write to output file '{output_filepath}'. Error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: An unexpected error occurred writing questions file: {e}", file=sys.stderr)
        return False