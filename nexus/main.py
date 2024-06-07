import os
import subprocess


def run_streamlit():
    # Determine the directory of the current file (e.g., the script this function is in)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    # Construct the path to streamlit_ui.py relative to this directory
    app_path = os.path.join(dir_path, "streamlit_main.py")

    command = ["streamlit", "run", app_path]
    process = subprocess.Popen(command)
    process.wait()
