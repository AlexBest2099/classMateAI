
import subprocess
import sys
def plot_analytics():
    subprocess.run([sys.executable, "analytics.py"])
    subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py"])
