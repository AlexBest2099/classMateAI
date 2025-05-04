# Hackaton

# Educational Document Analysis and Study Aid

## Overview

This project provides a system for uploading, analyzing, and tracking performance on educational documents like lecture notes, homework, and exams[cite: 1, 3, 16, 17, 18, 19, 21]. It extracts topics, subtopics, mistakes, and good examples from documents, stores them in a database, calculates performance metrics, and can generate study guides based on identified weaknesses or specific topics[cite: 1, 17, 18].

## Features

* **Document Processing:**
    * Backend processing pipeline (`combining_add_and_create.py`, `add_to_database.py`) analyzes documents from a specified `data/` directory using the Gemini API.
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
* **Web Interface Components (`index.html`, `script.js`, `style.css`): (Not functional)**
    * HTML/JS/CSS files suggest the presence or plan for a web-based document upload interface, separate from the main Tkinter application. This likely requires a dedicated backend API endpoint (e.g., `/api/upload`) for full functionality.

## Using the Application (Tkinter GUI Workflow)

This workflow focuses on using the primary Tkinter GUI application located in the repository directory.

1.  **Launch the Application:**
    * Navigate to the repository directory in your terminal, from where you downloaded **this** file.
    * Ensure your Gemini API key is correctly set in `config.py`.
    * Run the application using Python:
        ```bash
        python main.py
        ```

2.  **(Optional) Explore Initial State:**
    * The application comes with sample documents pre-loaded in the `Hackaton-master/Hackaton/data/` directory. These may have already been processed and populated into the `database.db` file.
    * You can inspect the current state of the database (`database.db`) using a recommended SQLite viewer (like the "SQLite by alexcvzz" extension in VS Code or DB Browser for SQLite) to view the existing data in tables such as `Mistakes`, `Good_Answers`, `Topics`, etc.

3.  **Process Your Documents (Optional):**
    * To analyze your own documents, place them into the your directory.
    * In the running GUI application, click the "Process New Files" button.
    * The system will identify unprocessed files in the `data/` directory, send them to the Gemini API for analysis, and update the `database.db` with extracted topics, mistakes, and good answers. Files already processed will be skipped.

4.  **View Performance Analytics:**
    * In the GUI, click the "Show Analytics" button.
    * The application will first run the `analytics.py` script in the background to ensure the metric files (`*.csv`, `*.json`) are up-to-date based on the current database contents.
    * Subsequently, it will launch the interactive Streamlit dashboard (`app.py`) in your default web browser, visualizing the calculated error rates and trends.

5.  **Generate a Customized Study Guide:**
    * In the GUI, click the "Refresh List" button. This queries the database and populates the listbox with topics that currently have associated mistakes recorded.
    * Select a topic of interest from the "Topics with Mistakes" list.
    * Click the "Generate Study Guide for Selected" button.
    * The application performs the following steps:
        * Exports the problem formulations of mistakes linked to the selected topic into a temporary file (`find_mistakes_topics.py`).
        * Identifies relevant source documents associated with the topic in the database.
        * Sends these documents and the mistake formulations to the Gemini API (`study_guide_generation.py`).
        * Saves the generated, cited study guide in Markdown format within the `study_guides/` directory. An attempt will be made to open this directory automatically.

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
