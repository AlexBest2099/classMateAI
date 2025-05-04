import tkinter as tk
from tkinter import ttk  # For themed widgets
from tkinter import messagebox
from tkinter import scrolledtext # For potentially showing logs or guides
import threading
import subprocess
import sys
import os
import time

# --- Import functions from other project files ---
# Ensure these files are in the same directory or Python path
try:
    from combining_add_and_create import process_and_add_file
    # We need to handle how plot_analytics starts Streamlit
    # from plot_analaytic import plot_analytics
    from find_mistakes_topics import get_topics_with_mistakes, export_questions_for_topic_to_txt
    from study_guide_generation import create_study_guide_md
except ImportError as e:
    messagebox.showerror("Import Error", f"Error importing required modules: {e}\n\nPlease ensure all .py files are in the same directory.")
    sys.exit(1)

# --- Configuration ---
DEFAULT_DB = 'database.db'
QUESTIONS_FILENAME = 'questions_for_study.txt' # Temp file for guide generation
STUDY_GUIDE_DIR = 'study_guides'
os.makedirs(STUDY_GUIDE_DIR, exist_ok=True) # Ensure study guide dir exists

# --- Main Application Class ---
class DocAssistantApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Educational Document Assistant")
        self.geometry("750x500") # Adjusted size

        # --- Styling ---
        self.style = ttk.Style(self)
        self.style.theme_use('clam') # Use a slightly more modern theme if available

        # --- Main Frame ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # --- Left Frame (Buttons) ---
        left_frame = ttk.Frame(main_frame, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False) # Prevent resizing based on content

        ttk.Label(left_frame, text="Actions", font=('Helvetica', 14, 'bold')).pack(pady=(0, 10))

        self.btn_process = ttk.Button(left_frame, text="Process New Files", command=self.run_process_files)
        self.btn_process.pack(pady=5, fill=tk.X)

        self.btn_analytics = ttk.Button(left_frame, text="Show Analytics", command=self.run_show_analytics)
        self.btn_analytics.pack(pady=5, fill=tk.X)

        # --- Right Frame (Topics and Guide Gen) ---
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        ttk.Label(right_frame, text="Topics with Mistakes", font=('Helvetica', 14, 'bold')).pack(pady=(0, 5))

        self.btn_refresh = ttk.Button(right_frame, text="Refresh List", command=self.load_topics_into_listbox)
        self.btn_refresh.pack(pady=(0, 5), anchor='nw')

        # Listbox with Scrollbar
        listbox_frame = ttk.Frame(right_frame)
        listbox_frame.pack(expand=True, fill=tk.BOTH, pady=(0, 10))

        self.topic_listbox = tk.Listbox(listbox_frame, height=15, exportselection=False)
        self.topic_listbox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.topic_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.topic_listbox.config(yscrollcommand=scrollbar.set)

        # Bind double-click or selection event if desired
        self.topic_listbox.bind('<Double-Button-1>', self.on_topic_select) # Double click

        self.btn_generate_guide = ttk.Button(right_frame, text="Generate Study Guide for Selected", command=self.on_topic_select)
        self.btn_generate_guide.pack(pady=5)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_var.set("Ready.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Initial Load ---
        self.load_topics_into_listbox()

    # --- Action Methods ---

    def update_status(self, message, clear_after_ms=None):
        """Updates the status bar. Optionally clears after a delay."""
        self.status_var.set(message)
        print(f"Status: {message}") # Also print to console
        if clear_after_ms:
            self.after(clear_after_ms, lambda: self.status_var.set("Ready."))

    def run_in_thread(self, target_func, *args):
        """Runs a function in a separate thread to avoid blocking the GUI."""
        thread = threading.Thread(target=target_func, args=args, daemon=True)
        thread.start()

    def load_topics_into_listbox(self):
        """Fetches topics with mistakes and populates the listbox."""
        self.update_status("Loading topics...")
        self.topic_listbox.delete(0, tk.END) # Clear existing items
        try:
            topics = get_topics_with_mistakes(DEFAULT_DB)
            if topics is None:
                self.topic_listbox.insert(tk.END, "Error loading topics!")
                self.update_status("Error loading topics.", 5000)
            elif not topics:
                self.topic_listbox.insert(tk.END, "No topics with mistakes found.")
                self.update_status("No topics with mistakes found.", 5000)
            else:
                for topic in topics:
                    self.topic_listbox.insert(tk.END, topic)
                self.update_status(f"Loaded {len(topics)} topics.", 3000)
        except Exception as e:
            self.topic_listbox.insert(tk.END, "Exception loading topics!")
            self.update_status(f"Exception loading topics: {e}", 5000)
            messagebox.showerror("Load Error", f"Failed to load topics: {e}")

    def _process_files_task(self):
        """Task to be run in background thread for processing files."""
        self.update_status("Processing new files...")
        self.set_buttons_state(tk.DISABLED)
        try:
            process_and_add_file()
            # After processing, refresh the topic list automatically
            self.after(100, self.load_topics_into_listbox) # Run in main thread
            self.update_status("File processing complete.", 5000)
            messagebox.showinfo("Processing Complete", "Finished processing files in 'data/' directory.")
        except Exception as e:
            self.update_status(f"Error during file processing: {e}", 5000)
            messagebox.showerror("Processing Error", f"An error occurred during file processing:\n{e}")
        finally:
            self.set_buttons_state(tk.NORMAL)

    def run_process_files(self):
        """Starts the file processing in a background thread."""
        self.run_in_thread(self._process_files_task)

    def _show_analytics_task(self):
        """Task to launch the analytics (Streamlit) process."""
        self.update_status("Launching analytics dashboard...")
        self.set_buttons_state(tk.DISABLED)
        try:
            # plot_analytics() directly calls Streamlit. We might need a more robust way
            # For simplicity, let's assume plot_analytic.py just runs streamlit
            # Find python executable to ensure it runs in the correct environment
            python_executable = sys.executable
            # Ensure analytics.py runs first if needed by plot_analytics
            subprocess.run([python_executable, "analytics.py"], check=True, capture_output=True)
            # Launch streamlit app
            # Use Popen to not block waiting for Streamlit to exit
            subprocess.Popen([python_executable, "-m", "streamlit", "run", "app.py"])
            self.update_status("Analytics dashboard launched (external window/browser).", 5000)
            messagebox.showinfo("Analytics Launched", "The Streamlit analytics dashboard should be opening in your web browser.")

        except FileNotFoundError:
             self.update_status("Error: streamlit or analytics.py/app.py not found.", 5000)
             messagebox.showerror("Launch Error", "Could not find Streamlit or necessary script files (analytics.py/app.py). Is Streamlit installed?")
        except subprocess.CalledProcessError as e:
             self.update_status(f"Error running analytics script: {e}", 5000)
             messagebox.showerror("Analytics Error", f"Error running analytics.py:\n{e.stderr.decode()}")
        except Exception as e:
             self.update_status(f"Error launching analytics: {e}", 5000)
             messagebox.showerror("Launch Error", f"An unexpected error occurred launching analytics:\n{e}")
        finally:
            self.set_buttons_state(tk.NORMAL)

    def run_show_analytics(self):
        """Starts the analytics launch in a background thread."""
        self.run_in_thread(self._show_analytics_task)

    def on_topic_select(self, event=None): # event is passed by bind
        """Handles selection of a topic from the listbox to generate a guide."""
        selected_indices = self.topic_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select a topic from the list first.")
            return

        selected_index = selected_indices[0]
        selected_topic = self.topic_listbox.get(selected_index)

        # Avoid triggering on error/info messages in listbox
        if "Error loading" in selected_topic or "No topics" in selected_topic:
             messagebox.showinfo("Info", "Cannot generate guide for this list entry.")
             return

        # Confirmation
        if messagebox.askyesno("Confirm Guide Generation", f"Generate study guide for:\n'{selected_topic}'?"):
            self.run_in_thread(self._generate_guide_task, selected_topic)

    def _generate_guide_task(self, topic_name):
        """Background task to export questions and generate the study guide."""
        self.update_status(f"Generating guide for '{topic_name}'...")
        self.set_buttons_state(tk.DISABLED)
        guide_path = None
        try:
            # Step 1: Export questions
            self.update_status(f"Exporting questions for '{topic_name}'...")
            export_success = export_questions_for_topic_to_txt(
                topic_name=topic_name,
                output_filepath=QUESTIONS_FILENAME,
                db_filepath=DEFAULT_DB
            )

            if not export_success:
                raise ValueError(f"Failed to export questions for topic '{topic_name}'.") # Raise error to be caught

            # Step 2: Generate guide
            self.update_status(f"Generating study guide Markdown for '{topic_name}'...")
            guide_path = create_study_guide_md(
                topic_name=topic_name,
                question_txt_filepath=QUESTIONS_FILENAME,
                db_filepath=DEFAULT_DB,
                output_dir=STUDY_GUIDE_DIR
            )

            if guide_path:
                self.update_status(f"Study guide saved: {guide_path}", 5000)
                messagebox.showinfo("Guide Generated", f"Study guide successfully generated and saved to:\n{guide_path}")
                # Optionally open the file or directory
                try:
                    os.startfile(os.path.dirname(guide_path)) # Windows
                except AttributeError:
                    try:
                       subprocess.run(['open', os.path.dirname(guide_path)], check=False) # macOS
                    except FileNotFoundError:
                       try:
                           subprocess.run(['xdg-open', os.path.dirname(guide_path)], check=False) # Linux
                       except FileNotFoundError:
                            print("Could not automatically open the output directory.")

            else:
                 raise RuntimeError("Study guide generation function returned None.")


        except Exception as e:
            self.update_status(f"Error generating guide for '{topic_name}': {e}", 5000)
            messagebox.showerror("Guide Generation Error", f"Failed to generate study guide for '{topic_name}':\n{e}")
        finally:
            # Clean up temporary questions file
            if os.path.exists(QUESTIONS_FILENAME):
                try:
                    os.remove(QUESTIONS_FILENAME)
                    print(f"Removed temporary file: {QUESTIONS_FILENAME}")
                except OSError as e:
                    print(f"Warning: Could not remove temporary file {QUESTIONS_FILENAME}: {e}")
            self.set_buttons_state(tk.NORMAL)

    def set_buttons_state(self, state):
        """Enable or disable buttons during operations (e.g., tk.DISABLED or tk.NORMAL)."""
        self.btn_process.config(state=state)
        self.btn_analytics.config(state=state)
        self.btn_refresh.config(state=state)
        self.btn_generate_guide.config(state=state)
        # Optionally disable listbox interaction too
        self.topic_listbox.config(state=state)


# --- Run the Application ---
if __name__ == "__main__":
    app = DocAssistantApp()
    app.mainloop()