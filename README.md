# Hackaton

# Educational Document Analysis and Study Aid

## Overview

This project provides a system for uploading, analyzing, and tracking performance on educational documents like lecture notes, homework, and exams. It extracts topics, subtopics, mistakes, and good examples from documents, stores them in a database, calculates performance metrics, and can generate study guides based on identified weaknesses or specific topics.

## Features

* **Document Upload:**
    * Web interface (`index.html`, `script.js`, `style.css`) for uploading documents (PDF, DOCX, TXT, Images supported by front-end).
    * Backend processing pipeline (`main.py`, `combining_add_and_create.py`) checks for duplicates in the database before processing.
    * Requires Gemini API Key for AI processing, entered via web UI or configured server-side.
* **Content Extraction:**
    * Uses Gemini (`add_to_database.py`) to analyze document content.
    * Extracts hierarchical structure: Subjects -> Topics -> Subtopics.
    * Identifies source locations (filename, filepath, page, details, keywords) within documents.
    * Extracts mistakes (description, type, details, problem formulation) and good answers (description, problem formulation) from relevant document types (homework, exams).
* **Mistake & Good Answer Tracking:** Identifies and extracts descriptions of mistakes and good answers from submitted work (like homework or exams), linking them to relevant topics/subtopics[cite: 1, 21].
* **Database Storage:**
    * Calculates error rates over time and per topic (`analytics.py`).
    * Exports metrics to CSV (`daily_metrics.csv`, `topic_metrics.csv`) and JSON (`latest_summary.json`).
    * Provides dashboards:
        * Streamlit dashboard (`app.py`) displaying error rates.
        * HTML/Plotly dashboard (`dashboard.html`) visualizing metrics from CSV files.
* **Performance Analytics:**
    * Calculates error rates over time and per topic (`analytics.py`).
    * Exports metrics to CSV (`daily_metrics.csv`, `topic_metrics.csv`) and JSON (`latest_summary.json`).
    * Provides dashboards:
        * Streamlit dashboard (`app.py`) displaying error rates.
        * HTML/Plotly dashboard (`dashboard.html`) visualizing metrics from CSV files.
* **Visualization Dashboard:** Displays performance metrics, such as error rate over time and by topic, using charts (implemented via Streamlit in `app.py` and/or Plotly in `dashboard.html`)[cite: 16, 10].
* **Study Guide Generation:**
    * Generates comprehensive Markdown study guides for specific topics (`study_guide_generation.py`).
    * Synthesizes information from relevant database-linked documents and a user-provided question file.
    * Cites source documents within the generated guide.

## Workflow

1.  **Upload:** User uploads a document via the web interface (`index.html`) or places it in the `data/` directory.
2.  **Processing Trigger:** `main.py` likely triggers `combining_add_and_create.py`.
3.  **Duplicate Check:** The script checks if the file already exists in the `Sources` table of the database (`database.db`).
4.  **AI Analysis:** If new, the file is sent to the Gemini API along with context (`create_database.py` script for schema understanding) via `add_to_database.py`.
5.  **JSON Response:** Gemini returns a structured JSON (`response_output.json`) containing extracted content, mistakes, and good answers.
6.  **Database Population:** `create_database_from_json` function within `create_database.py` parses the JSON and inserts/updates the SQLite database.
7.  **Analytics Calculation:** `analytics.py` is run (manually or triggered) to query the database and generate updated CSV/JSON metric files.
8.  **Dashboard Display:** Users view `dashboard.html` or run the Streamlit app (`app.py`) which reads the metric files to display visualizations.
9.  **Study Guide Request:** User runs `study_guide_generation.py` with a topic and question file path. The script fetches relevant file paths from the DB, uploads them to Gemini, and generates a cited Markdown guide.


## File Structure/Components

* **`main.py`**: Main script to initiate the processing workflow[cite: 19].
* **`combining_add_and_create.py`**: Orchestrates the processing of files in the `data` directory, checking for existence in the DB and calling the analysis/DB insertion logic[cite: 21].
* **`add_to_database.py`**: Handles interaction with the Gemini API to analyze a document (PDF) and calls the database population function[cite: 3].
* **`create_database.py`**: Defines the SQLite database schema and provides functions to initialize the schema and populate it from a JSON input file[cite: 1]. Contains functions to check if a file already exists in the DB.
* **`study_guide_generation.py`**: Generates study guides in Markdown format for a given topic using Gemini, referencing relevant files from the database and a user-provided question file[cite: 18].
* **`analytics.py`**: Queries the database to calculate performance metrics (daily and per-topic error rates) and exports them to CSV and JSON files[cite: 17].
* **`app.py`**: Streamlit application to display the performance dashboard using data from the generated CSV files[cite: 16].
* **`index.html`**: Main HTML page for the document upload interface[cite: 4].
* **`dashboard.html`**: HTML page for displaying the performance dashboard using Plotly.js[cite: 10].
* **`script.js`**: JavaScript for handling file uploads, drag-and-drop, API key input, form submission, and updating the UI on `index.html`[cite: 13]. Also includes JavaScript for fetching data and rendering Plotly charts on `dashboard.html`.
* **`style.css`**: CSS for styling the web interface (`index.html`)[cite: 15].
* **`data/`**: Directory likely containing the input educational documents (e.g., `Automation_P02_SensorConcepts.pdf`)[cite: 22].
* **`*.db`**: SQLite database file(s) generated by the scripts (e.g., `database.db`, `database_with_formulation.db`, `automation_concepts.db`)[cite: 1, 3].
* **`*.json`**: JSON files used for intermediate data representation or output (e.g., `response_output.json`, `test.json`, `test_with_formulation.json`, `latest_summary.json`)[cite: 2, 9, 14, 6].
* **`*.csv`**: CSV files containing calculated metrics (e.g., `daily_metrics.csv`, `topic_metrics.csv`, `Daily_Metrics_test.csv`, `Topic_Metrics_test.csv`)[cite: 5, 12, 7, 8].
* **`README.md`**: This file.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Hackaton-master
    ```
2.  **Install Dependencies:** Ensure you have Python installed. Install necessary libraries (based on imports):
    ```bash
    pip install google-generativeai pandas streamlit plotly # Add any other missing libraries based on script imports
    ```
3.  **API Key:**
    * Set the `GOOGLE_API_KEY` environment variable[cite: 3].
    * Alternatively, modify scripts like `add_to_database.py` or `study_guide_generation.py` (using a `config.py` or directly) to include your Gemini API key (less secure)[cite: 3, 18]. The front-end also requires the API key to be entered[cite: 4].
4.  **Data:** Place your educational documents (e.g., PDFs) into the `data/` directory[cite: 21].

## Usage

1.  **Process Documents & Populate Database:**
    * Run the main processing script:
        ```bash
        python main.py
        ```
        This script (via `combining_add_and_create.py`) iterates through files in the `data/` directory, checks if they are already processed, calls the Gemini API for analysis (`add_to_database.py`), gets a JSON output, and populates the SQLite database (`create_database.py`)[cite: 19, 21, 3, 1].
2.  **Calculate Analytics:**
    * Run the analytics script to generate/update the metrics CSV files:
        ```bash
        python analytics.py
        ```
        This reads from the database and outputs `daily_metrics.csv`, `topic_metrics.csv`, and `latest_summary.json`[cite: 17].
3.  **View Dashboard:**
    * **Streamlit:** Run the Streamlit app:
        ```bash
        streamlit run app.py
        ```
        This will launch a web server displaying the dashboard based on `app.py`[cite: 16].
    * **HTML/Plotly:** Open `dashboard.html` in your web browser. Ensure the `Daily_Metrics_test.csv` and `Topic_Metrics_test.csv` files (or the non-test versions if `dashboard.html` is updated) are present in the same directory[cite: 10].
4.  **Upload via Web Interface:**
    * Serve the `index.html` file using a simple HTTP server or open it directly in your browser (functionality requiring backend interaction like `/api/upload` might need a proper server setup).
    * Use the interface to select a document type, choose a file, enter your Gemini API key, and upload[cite: 4, 13].
5.  **Generate Study Guides:**
    * Modify and run `study_guide_generation.py`, providing the desired topic name and the path to a text file containing relevant questions[cite: 18].
        ```python
        # Example within study_guide_generation.py or a separate script
        import study_guide_generation
        study_guide_generation.create_study_guide_md(
            topic_name="Specific Topic Name",
            question_txt_filepath="path/to/your/questions.txt",
            db_filepath="database.db", # Adjust if needed
            output_dir="study_guides/"
        )
        ```

## Dependencies (Inferred from Imports)

* `google.generativeai` [cite: 3, 18]
* `sqlite3` [cite: 1, 17, 18]
* `json` [cite: 1, 3, 17]
* `os` [cite: 1, 3, 18, 21]
* `datetime` [cite: 1]
* `pandas` [cite: 16, 17]
* `streamlit` [cite: 16]
* `plotly` / `plotly.express` [cite: 16] (also used via CDN in `dashboard.html` [cite: 10])
* `re` (regular expressions) [cite: 18]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

(Specify License - e.g., MIT, Apache 2.0, etc. - If applicable) - Defaulting to standard placeholder as no license file was provided.
