import logging

import streamlit as st


# Define a custom log handler
class NexusUILogHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        # Check if the new message is the same as the last one
        if msg != st.session_state.last_log_message:
            st.session_state.log_messages += msg + "\n"
            # Update the last log message
            st.session_state.last_log_message = msg


# Configure logger
logger = logging.getLogger("Nexus Logger")
logger.setLevel(logging.INFO)  # Set your logging level
formatter = logging.Formatter("%(levelname)s - %(message)s")

# Create our custom handler and set the formatter
handler = NexusUILogHandler()
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)


def display_logs_in_container():
    # Display logs from session state
    st.text_area("Log Messages", value=st.session_state.log_messages, height=600)
