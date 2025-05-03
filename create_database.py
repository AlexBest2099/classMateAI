import json
import sqlite3
import os
import datetime # For default date

# --- Database Schema Definitions (Constants) ---

SQL_CREATE_SUBJECTS = """
CREATE TABLE IF NOT EXISTS Subjects (
    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL UNIQUE,
    subject_description TEXT
);
"""

SQL_CREATE_TOPICS = """
CREATE TABLE IF NOT EXISTS Topics (
    topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,      -- Link to Subjects table
    topic_name TEXT NOT NULL,
    topic_description TEXT,
    FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE CASCADE,
    UNIQUE (subject_id, topic_name) -- Topic names unique within a subject
);
"""

SQL_CREATE_SUBTOPICS = """
CREATE TABLE IF NOT EXISTS Subtopics (
    subtopic_id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,        -- Link to Topics table
    subtopic_name TEXT NOT NULL,
    subtopic_description TEXT,
    FOREIGN KEY (topic_id) REFERENCES Topics(topic_id) ON DELETE CASCADE,
    UNIQUE (topic_id, subtopic_name) -- Subtopic names unique within a topic
);
"""

SQL_CREATE_SOURCES = """
CREATE TABLE IF NOT EXISTS Sources (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    UNIQUE (filepath, filename)       -- Ensures unique source locations
);
"""

SQL_CREATE_TOPIC_SOURCE_LOCATIONS = """
CREATE TABLE IF NOT EXISTS Topic_Source_Locations (
    topic_location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    page_number INTEGER,
    location_description TEXT,
    FOREIGN KEY (topic_id) REFERENCES Topics(topic_id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES Sources(source_id) ON DELETE CASCADE,
    UNIQUE (topic_id, source_id, page_number, location_description)
);
"""

SQL_CREATE_SUBTOPIC_SOURCE_LOCATIONS = """
CREATE TABLE IF NOT EXISTS Subtopic_Source_Locations (
    subtopic_location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subtopic_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    page_number INTEGER,
    location_detail TEXT,
    keywords TEXT,
    FOREIGN KEY (subtopic_id) REFERENCES Subtopics(subtopic_id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES Sources(source_id) ON DELETE CASCADE,
    UNIQUE (subtopic_id, source_id, page_number, location_detail)
);
"""

# MODIFIED: Added problem_formulation to Mistakes table
SQL_CREATE_MISTAKES = """
CREATE TABLE IF NOT EXISTS Mistakes (
    mistake_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,       -- FK to Sources (the homework/exam file)
    topic_id INTEGER NOT NULL,        -- FK to Topics (relevant topic)
    subtopic_id INTEGER,              -- FK to Subtopics (relevant subtopic, nullable)
    mistake_description TEXT NOT NULL,-- Description of the error
    problem_formulation TEXT,         -- NEW: The actual text of the problem/exercise (nullable)
    mistake_type TEXT,                -- Category of error (e.g., 'Calculation', 'Conceptual', 'Syntax')
    page_number INTEGER,              -- Page where mistake occurred
    location_detail TEXT,             -- Specific location (row, question number, etc.)
    mistake_details TEXT,             -- General details about the mistake (optional)
    date_recorded DATE DEFAULT CURRENT_DATE, -- When the mistake was logged
    FOREIGN KEY (source_id) REFERENCES Sources(source_id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES Topics(topic_id) ON DELETE SET NULL,
    FOREIGN KEY (subtopic_id) REFERENCES Subtopics(subtopic_id) ON DELETE SET NULL
);
"""

# MODIFIED: Added problem_formulation to Good_Answers table
SQL_CREATE_GOOD_ANSWERS = """
CREATE TABLE IF NOT EXISTS Good_Answers (
    good_answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,       -- FK to Sources (the homework/exam file)
    topic_id INTEGER NOT NULL,        -- FK to Topics (relevant topic)
    subtopic_id INTEGER,              -- FK to Subtopics (relevant subtopic, nullable)
    answer_description TEXT NOT NULL, -- Description of why it's a good answer/example
    problem_formulation TEXT,         -- NEW: The actual text of the problem/exercise (nullable)
    page_number INTEGER,              -- Page where answer is found
    location_detail TEXT,             -- Specific location (row, question number, etc.)
    date_recorded DATE DEFAULT CURRENT_DATE, -- When the example was logged
    FOREIGN KEY (source_id) REFERENCES Sources(source_id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES Topics(topic_id) ON DELETE SET NULL,
    FOREIGN KEY (subtopic_id) REFERENCES Subtopics(subtopic_id) ON DELETE SET NULL
);
"""


def initialize_database_schema(db_file_path: str) -> bool:
    """
    Connects to the SQLite database and creates all necessary tables
    including Mistakes and Good_Answers with the problem_formulation field.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Execute CREATE TABLE statements for the full schema
        cursor.execute(SQL_CREATE_SUBJECTS)
        cursor.execute(SQL_CREATE_TOPICS)
        cursor.execute(SQL_CREATE_SUBTOPICS)
        cursor.execute(SQL_CREATE_SOURCES)
        cursor.execute(SQL_CREATE_TOPIC_SOURCE_LOCATIONS)
        cursor.execute(SQL_CREATE_SUBTOPIC_SOURCE_LOCATIONS)
        cursor.execute(SQL_CREATE_MISTAKES) # Uses updated constant
        cursor.execute(SQL_CREATE_GOOD_ANSWERS) # Uses updated constant

        conn.commit()
        print(f"Database schema (with Problem Formulation) initialized successfully in '{db_file_path}'.")
        return True

    except sqlite3.Error as e:
        print(f"Database error during schema initialization: {e}")
        if conn: conn.rollback()
        return False
    except Exception as e:
        print(f"An unexpected error occurred during schema initialization: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

def create_database_from_json(json_file_path: str, db_file_path: str) -> bool:
    """
    Initializes the database schema (if needed) and populates it by parsing
    a JSON file containing 'content', 'mistakes', and 'good_answers' sections.
    Mistakes and Good Answers can now include a 'problem_formulation' field.

    Assumes JSON structure:
    {
      "content": [ ... ],
      "mistakes": [
          {
              "source_filename": "...", "source_filepath": "...",
              "page": ..., "location_detail": "...",
              "description": "...", "type": "...", "details": "...",
              "problem_formulation": "The actual text of the exercise...", # Optional
              "relevant_topic": "Topic Name",
              "relevant_subtopic": "Subtopic Name" # Optional
          }
       ],
      "good_answers": [
          {
              "source_filename": "...", "source_filepath": "...",
              "page": ..., "location_detail": "...",
              "description": "...",
              "problem_formulation": "The actual text of the exercise...", # Optional
              "relevant_topic": "Topic Name",
              "relevant_subtopic": "Subtopic Name" # Optional
          }
      ]
    }

    Args:
        json_file_path: The path to the input JSON file.
        db_file_path: The path where the SQLite database file should be created/updated.

    Returns:
        True if the database was populated successfully, False otherwise.
    """

    # --- Step 1: Ensure Database Schema Exists ---
    print(f"Initializing database schema for '{db_file_path}'...")
    if not initialize_database_schema(db_file_path):
        print("Failed to initialize database schema. Aborting population.")
        return False
    print("Schema check/initialization complete.")

    # --- Step 2: Load JSON Data ---
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                 raise ValueError("JSON must be an object.")
            content_data = data.get("content", [])
            mistakes_data = data.get("mistakes", [])
            good_answers_data = data.get("good_answers", [])

    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_file_path}")
        return False
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: Could not decode JSON or invalid structure in {json_file_path}: {e}")
        return False
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return False

    # --- Helper Functions (nested) ---
    # Content helpers (unchanged)
    def _get_or_create_subject(cursor, subject_name, description=None):
        cursor.execute("SELECT subject_id FROM Subjects WHERE subject_name = ?", (subject_name,))
        result = cursor.fetchone(); return result[0] if result else cursor.execute("INSERT INTO Subjects (subject_name, subject_description) VALUES (?, ?)", (subject_name, description)).lastrowid

    def _get_or_create_topic(cursor, subject_id, topic_name, description=None):
        cursor.execute("SELECT topic_id FROM Topics WHERE subject_id = ? AND topic_name = ?", (subject_id, topic_name))
        result = cursor.fetchone(); return result[0] if result else cursor.execute("INSERT INTO Topics (subject_id, topic_name, topic_description) VALUES (?, ?, ?)", (subject_id, topic_name, description)).lastrowid

    def _get_or_create_subtopic(cursor, topic_id, subtopic_name, description=None):
        cursor.execute("SELECT subtopic_id FROM Subtopics WHERE topic_id = ? AND subtopic_name = ?", (topic_id, subtopic_name))
        result = cursor.fetchone(); return result[0] if result else cursor.execute("INSERT INTO Subtopics (topic_id, subtopic_name, subtopic_description) VALUES (?, ?, ?)", (topic_id, subtopic_name, description)).lastrowid

    def _get_or_create_source(cursor, filename, filepath):
        cursor.execute("SELECT source_id FROM Sources WHERE filename = ? AND filepath = ?", (filename, filepath))
        result = cursor.fetchone(); return result[0] if result else cursor.execute("INSERT INTO Sources (filename, filepath) VALUES (?, ?)", (filename, filepath)).lastrowid

    def _link_topic_to_source_location(cursor, topic_id, source_id, page=None, location_desc=None):
        cursor.execute("INSERT OR IGNORE INTO Topic_Source_Locations (topic_id, source_id, page_number, location_description) VALUES (?, ?, ?, ?)", (topic_id, source_id, page, location_desc))

    def _link_subtopic_to_source_location(cursor, subtopic_id, source_id, page=None, detail=None, keywords=None):
        cursor.execute("INSERT OR IGNORE INTO Subtopic_Source_Locations (subtopic_id, source_id, page_number, location_detail, keywords) VALUES (?, ?, ?, ?, ?)", (subtopic_id, source_id, page, detail, keywords))

    # ID Lookup helpers (unchanged)
    def _get_topic_id_by_name(cursor, topic_name):
        cursor.execute("SELECT topic_id FROM Topics WHERE topic_name = ?", (topic_name,))
        result = cursor.fetchone(); return result[0] if result else None

    def _get_subtopic_id_by_name(cursor, topic_id, subtopic_name):
        if not topic_id: return None
        cursor.execute("SELECT subtopic_id FROM Subtopics WHERE topic_id = ? AND subtopic_name = ?", (topic_id, subtopic_name))
        result = cursor.fetchone(); return result[0] if result else None

    # MODIFIED: Mistake creation helper accepts problem_formulation
    def _create_mistake(cursor, source_id, topic_id, subtopic_id, desc, problem_formulation, type, page, location, details):
        if not source_id or not topic_id:
            print(f"Warning: Skipping mistake creation due to missing source_id or topic_id. Desc: {desc}")
            return
        cursor.execute("""
            INSERT INTO Mistakes
            (source_id, topic_id, subtopic_id, mistake_description, problem_formulation, mistake_type, page_number, location_detail, mistake_details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (source_id, topic_id, subtopic_id, desc, problem_formulation, type, page, location, details))

    # MODIFIED: Good answer creation helper accepts problem_formulation
    def _create_good_answer(cursor, source_id, topic_id, subtopic_id, desc, problem_formulation, page, location):
        if not source_id or not topic_id:
            print(f"Warning: Skipping good answer creation due to missing source_id or topic_id. Desc: {desc}")
            return
        cursor.execute("""
            INSERT INTO Good_Answers
            (source_id, topic_id, subtopic_id, answer_description, problem_formulation, page_number, location_detail)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (source_id, topic_id, subtopic_id, desc, problem_formulation, page, location))
        # print(f"    Created good answer record (ID: {cursor.lastrowid})") # Optional logging


    # --- Step 3: Populate Database ---
    conn = None
    try:
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        # --- Process Content Section ---
        print("Processing 'content' section...")
        # ... (existing logic for subjects, topics, subtopics, locations - unchanged) ...
        for subject_data in content_data:
            subject_name = subject_data.get("subject_name")
            if not subject_name: continue
            subject_id = _get_or_create_subject(cursor, subject_name, subject_data.get("subject_description"))
            for topic_data in subject_data.get("topics", []):
                topic_name = topic_data.get("topic_name")
                if not topic_name: continue
                topic_id = _get_or_create_topic(cursor, subject_id, topic_name, topic_data.get("topic_description"))
                for loc_data in topic_data.get("source_locations", []):
                    filename = loc_data.get("filename"); filepath = loc_data.get("filepath")
                    if not filename or not filepath: continue
                    source_id = _get_or_create_source(cursor, filename, filepath)
                    _link_topic_to_source_location(cursor, topic_id, source_id, loc_data.get("page"), loc_data.get("location_description"))
                for subtopic_data in topic_data.get("subtopics", []):
                    subtopic_name = subtopic_data.get("subtopic_name")
                    if not subtopic_name: continue
                    subtopic_id = _get_or_create_subtopic(cursor, topic_id, subtopic_name, subtopic_data.get("subtopic_description"))
                    for sub_loc_data in subtopic_data.get("source_locations", []):
                         filename = sub_loc_data.get("filename"); filepath = sub_loc_data.get("filepath")
                         if not filename or not filepath: continue
                         source_id = _get_or_create_source(cursor, filename, filepath)
                         _link_subtopic_to_source_location(cursor, subtopic_id, source_id, sub_loc_data.get("page"), sub_loc_data.get("location_detail"), sub_loc_data.get("keywords"))
        print("'content' section processing complete.")

        # --- Process Mistakes Section ---
        print("Processing 'mistakes' section...")
        for mistake_data in mistakes_data:
            source_filename = mistake_data.get("source_filename"); source_filepath = mistake_data.get("source_filepath")
            desc = mistake_data.get("description"); topic_name = mistake_data.get("relevant_topic")
            if not source_filename or not source_filepath or not desc or not topic_name:
                print(f"Warning: Skipping mistake due to missing required fields. Desc: {desc}")
                continue

            source_id = _get_or_create_source(cursor, source_filename, source_filepath)
            topic_id = _get_topic_id_by_name(cursor, topic_name)
            if not topic_id:
                print(f"Warning: Could not find topic '{topic_name}' for mistake. Skipping. Desc: {desc}")
                continue

            subtopic_id = None; subtopic_name = mistake_data.get("relevant_subtopic")
            if subtopic_name:
                subtopic_id = _get_subtopic_id_by_name(cursor, topic_id, subtopic_name)
                # Optional: Warn if subtopic not found but still proceed with topic link
                # if not subtopic_id: print(f"Warning: Subtopic '{subtopic_name}' not found under topic '{topic_name}' for mistake.")

            # MODIFIED: Get problem formulation from JSON
            problem_formulation = mistake_data.get("problem_formulation") # Gets None if not present

            # MODIFIED: Pass problem formulation to helper function
            _create_mistake(
                cursor,
                source_id,
                topic_id,
                subtopic_id,
                desc,
                problem_formulation, # Pass the text here
                mistake_data.get("type"),
                mistake_data.get("page"),
                mistake_data.get("location_detail"),
                mistake_data.get("details")
            )
        print("'mistakes' section processing complete.")

        # --- Process Good Answers Section ---
        print("Processing 'good_answers' section...")
        for answer_data in good_answers_data:
            source_filename = answer_data.get("source_filename")
            source_filepath = answer_data.get("source_filepath")
            desc = answer_data.get("description")
            topic_name = answer_data.get("relevant_topic")

            if not source_filename or not source_filepath or not desc or not topic_name:
                print(f"Warning: Skipping good answer due to missing required fields (source_filename, source_filepath, description, relevant_topic). Desc: {desc}")
                continue

            source_id = _get_or_create_source(cursor, source_filename, source_filepath)
            topic_id = _get_topic_id_by_name(cursor, topic_name)
            if not topic_id:
                 print(f"Warning: Could not find topic '{topic_name}' for good answer. Skipping. Desc: {desc}")
                 continue

            subtopic_id = None
            subtopic_name = answer_data.get("relevant_subtopic")
            if subtopic_name: # Only look for subtopic if topic was found and subtopic name provided
                subtopic_id = _get_subtopic_id_by_name(cursor, topic_id, subtopic_name)
                if not subtopic_id:
                     print(f"Warning: Could not find subtopic '{subtopic_name}' under topic '{topic_name}' for good answer. Linking to topic only.")

            # MODIFIED: Get problem formulation from JSON
            problem_formulation = answer_data.get("problem_formulation") # Gets None if not present

            # MODIFIED: Pass problem formulation to helper function
            _create_good_answer(
                cursor,
                source_id,
                topic_id,
                subtopic_id, # Can be None
                desc,
                problem_formulation, # Pass the text here
                answer_data.get("page"),
                answer_data.get("location_detail")
            )
        print("'good_answers' section processing complete.")


        conn.commit()
        print(f"Successfully populated database '{db_file_path}' from '{json_file_path}' (with Problem Formulation).")
        return True

    except sqlite3.Error as e:
        print(f"Database error occurred during population: {e}")
        if conn: conn.rollback()
        return False
    except Exception as e:
        print(f"An unexpected error occurred during database population: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

# --- check_file_exists_in_db function remains unchanged ---
def check_file_exists_in_db(db_filepath: str, filename_to_check: str) -> bool:
    """
    Checks if a record with the given filename exists in the Sources table
    of the specified SQLite database.

    Args:
        db_filepath: Path to the SQLite database file (e.g., 'database.db').
        filename_to_check: The filename to search for (e.g., 'hw1.pdf').

    Returns:
        True if at least one record with that filename exists, False otherwise.
        Returns False also if a database error occurs.
    """
    conn = None
    exists = False
    try:
        if not os.path.exists(db_filepath):
            print(f"Error: Database file not found at '{db_filepath}'")
            return False

        conn = sqlite3.connect(db_filepath)
        cursor = conn.cursor()

        sql_query = "SELECT COUNT(*) FROM Sources WHERE filename = ?"

        cursor.execute(sql_query, (filename_to_check,))

        result = cursor.fetchone()

        if result and result[0] > 0:
            exists = True

    except sqlite3.Error as e:
        print(f"An SQLite error occurred: {e}")
        exists = False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exists = False
    finally:
        if conn:
            conn.close()

    return exists



def get_topic_id_pairs_as_string(db_filepath: str = 'database.db') -> str:
    """
    Retrieves all topic IDs and names from the Topics table in the specified
    SQLite database and returns them as a single string, with each pair
    formatted as "Topic Name: Topic ID" on a new line.

    Args:
        db_filepath: The path to the SQLite database file.
                     Defaults to 'database.db'.

    Returns:
        A string containing all topic name/ID pairs, sorted by topic name,
        each on a new line (e.g., "Topic A: 1\nTopic B: 2").
        Returns an error message string if the database/table cannot be accessed
        or if no topics are found.
    """
    if not os.path.exists(db_filepath):
        return f"Error: Database file not found at '{db_filepath}'"

    conn = None
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_filepath)
        cursor = conn.cursor()

        # Check if the Topics table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Topics';")
        if cursor.fetchone() is None:
            return f"Error: 'Topics' table not found in database '{db_filepath}'. Was the database initialized?"

        # Query to get topic ID and name, sorted by name
        # Selects all entries, relying on schema uniqueness or listing duplicates if they exist
        cursor.execute("SELECT topic_id, topic_name FROM Topics ORDER BY topic_name;")

        # Fetch all results. fetchall() returns a list of tuples.
        # Example: [(1, 'Calculus'), (3, 'Differentiation'), (2, 'Linear Algebra')]
        results = cursor.fetchall()

        if not results:
            return f"No topics found in the 'Topics' table of database '{db_filepath}'."

        # Format each pair (name: id) and store in a list
        formatted_pairs = []
        for topic_id, topic_name in results:
            # Ensure topic_name is not None or empty before formatting
            if topic_name:
                formatted_pairs.append(f"{topic_name}: {topic_id}")
            else:
                # Optionally handle cases where topic_name might be NULL
                formatted_pairs.append(f"Unknown Topic: {topic_id}")

        # Join the list of formatted strings with newline characters
        return '\n'.join(formatted_pairs)

    except sqlite3.Error as e:
        # Handle potential database errors
        return f"Error: Database error occurred while querying topics - {e}"
    except Exception as e:
        # Catch any other unexpected errors
        return f"Error: An unexpected error occurred - {e}"
    finally:
        # Ensure the database connection is closed
        if conn:
            conn.close()
