# Hackaton

# Educational Document Analysis and Study Aid

## Overview

This project provides a system for uploading, analyzing, and tracking performance on educational documents like lecture notes, homework, and exams[cite: 1, 3, 16, 17, 18, 19, 21]. It extracts topics, subtopics, mistakes, and good examples from documents, stores them in a database, calculates performance metrics, and can generate study guides based on identified weaknesses or specific topics[cite: 1, 17, 18].

## Features

* **Document Processing:**
    * Backend processing pipeline (`combining_add_and_create.py`, `add_to_database.py`) analyzes documents (PDF, TXT supported) from a specified `data/` directory using the Gemini API.
    * Checks for duplicates in the database before processing.
    * Requires Gemini API Key configuration (`config.py`).
* **Content Extraction & Database Storage:**
    * Extracts hierarchical structure (Subjects -> Topics -> Subtopics) and source location details.
    * Identifies and extracts mistakes (description, type, problem formulation) and good answers from relevant documents.
    * Stores extracted information in an SQLite database (`database.db`) using a defined schema (`create_database.py`).
* **Tkinter GUI Application (`Hackaton-master/Hackaton/main.py`):**
    * Provides the primary user interface for interacting with the system.
    * Allows users to trigger the processing of new files in the `data/` directory.
    * Displays topics where mistakes have been recorded.
    * Initiates the generation of study guides for selected topics.
    * Provides a button to launch the performance analytics dashboard.
* **Performance Analytics & Visualization:**
    * Calculates error rates over time and per topic (`analytics.py`).
    * Exports metrics to CSV (`daily_metrics.csv`, `topic_metrics.csv`) and JSON (`latest_summary.json`).
    * Provides multiple dashboard options:
        * **Streamlit Dashboard (`app.py`):** Launched via the Tkinter GUI or command line, displaying interactive charts based on `daily_metrics.csv` and `topic_metrics.csv`.
        * **HTML/Plotly Dashboard (`dashboard.html`):** A static HTML page displaying charts based on CSV files (requires `Daily_Metrics_test.csv` and `Topic_Metrics_test.csv` by default).
* **Study Guide Generation:**
    * Generates comprehensive Markdown study guides for specific topics (`study_guide_generation.py`) using the Gemini API, triggered via the Tkinter GUI.
    * Synthesizes information from relevant database-linked documents and questions extracted from recorded mistakes.
    * Cites source documents within the generated guide.
* **Web Interface Components (`index.html`, `script.js`, `style.css`):**
    * HTML/JS/CSS files suggest the presence or plan for a web-based document upload interface, separate from the main Tkinter application. This likely requires a dedicated backend API endpoint (e.g., `/api/upload`) for full functionality.

## Workflow (Focusing on Tkinter GUI)

1.  **Data Preparation:** Place educational documents into the `Hackaton-master/Hackaton/data/` directory.
2.  **Launch GUI:** Navigate to the `Hackaton-master/Hackaton/` directory and run `python main.py`.
3.  **Process Files:** Click the "Process New Files" button in the GUI. This triggers `process_and_add_file` (`combining_add_and_create.py`), which analyzes new files in the `data/` directory using Gemini (`add_to_database.py`) and updates the database (`create_database.py`).
4.  **View Analytics:** Click the "Show Analytics" button. This runs `analytics.py` to update metrics files and then launches the Streamlit dashboard (`app.py`) in a web browser.
5.  **Generate Study Guide:**
    * Click "Refresh List" to load topics with mistakes.
    * Select a topic from the list.
    * Click "Generate Study Guide for Selected".
    * The application exports relevant questions (`find_mistakes_topics.py`) and then calls the study guide generation function (`study_guide_generation.py`), saving the result in the `study_guides/` directory.

## File Structure/Components

*(This section remains largely the same as before, describing the purpose of each key file like `main.py` (Tkinter), `combining_add_and_create.py`, `add_to_database.py`, `create_database.py`, `analytics.py`, `app.py`, `study_guide_generation.py`, `index.html`, `dashboard.html`, etc.)*

* **`Hackaton-master/Hackaton/main.py`**: **Primary Tkinter GUI application** for user interaction.
* **`Hackaton-master/main.py`**: Simple script to trigger backend processing directly.
* `combining_add_and_create.py`: Orchestrates processing files in `data/`.
* `add_to_database.py`: Interacts with Gemini API for document analysis.
* `create_database.py`: Defines DB schema, initializes, populates from JSON, utility functions.
* `analytics.py`: Calculates and exports performance metrics.
* `app.py`: Streamlit dashboard application.
* `study_guide_generation.py`: Generates Markdown study guides.
* `find_mistakes_topics.py`: Finds topics with mistakes and exports questions.
* `index.html`, `script.js`, `style.css`: Files for a separate web interface component.
* `dashboard.html`: HTML/Plotly dashboard.
* `config.py`: For API key storage (used by Tkinter GUI path).
* `data/`: Directory for input documents.
* `study_guides/`: Output directory for generated guides.
* `database.db`: SQLite database file.
* `*.csv`, `*.json`: Analytics output files.

## Setup

1.  **Clone the repository.**
2.  **Navigate to the `Hackaton-master/Hackaton/` directory.** (This contains the main Tkinter application)
    ```bash
    cd Hackaton-master/Hackaton
    ```
3.  **Install Dependencies:**
    ```bash
    pip install google-generativeai pandas streamlit plotly # Add other missing libraries if necessary
    ```
    *(Ensure Tkinter is available in your Python installation)*
4.  **API Key:** Create a `config.py` file in the `Hackaton-master/Hackaton/` directory with your Gemini API key:
    ```python
    # config.py
    api_key='YOUR_GEMINI_API_KEY'
    ```
5.  **Data:** Place educational documents into the `Hackaton-master/Hackaton/data/` directory.

## Usage (Tkinter GUI Recommended)

1.  **Ensure you are in the `Hackaton-master/Hackaton/` directory.**
2.  **Run the Tkinter application:**
    ```bash
    python main.py
    ```
3.  **Use the GUI:**
    * Click "Process New Files" to analyze documents in the `data/` folder.
    * Click "Show Analytics" to calculate metrics and view the Streamlit dashboard.
    * Click "Refresh List", select a topic, and click "Generate Study Guide..." to create study materials.

## Dependencies (Inferred from Imports)

* `google.generativeai`
* `sqlite3`
* `json`
* `os`
* `datetime`
* `pandas`
* `streamlit`
* `plotly` / `plotly.express`
* `re` (regular expressions)
* `tkinter`, `tkinter.ttk`
* `threading`
* `subprocess`
* `sys`
* *(Potentially others depending on which scripts are executed)*

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
