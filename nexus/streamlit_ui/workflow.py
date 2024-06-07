import streamlit as st
from barfi import st_barfi

from nexus.streamlit_ui.cache import get_nexus
from nexus.streamlit_ui.workflow_logging import display_logs_in_container


def workflow_page(username, win_height):
    chat = get_nexus()
    user = chat.get_participant(username)
    if user is None:
        st.error("Invalid user")
        st.stop()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Agent Workflow")
        workflow = st_barfi(
            base_blocks=[],
            compute_engine=True,
        )

    with col2:
        st.header("Agent Workflow Logs")
        display_logs_in_container()
