import time

import streamlit as st
from streamlit_js_eval import set_cookie
from streamlit_js_eval import streamlit_js_eval as st_js
from streamlit_ui.actions import actions_page
from streamlit_ui.knowledge import knowledge_page
from streamlit_ui.login import login_page
from streamlit_ui.memory import memory_page
from streamlit_ui.profile import profile_page
from streamlit_ui.thought_templates import thought_templates_page
from streamlit_ui.usage import usage_page
from streamlit_ui.workflow import workflow_page

from nexus.streamlit_ui.agent_chat import chat_page
from nexus.streamlit_ui.assistants_chat import assistants_page


def main():
    st.set_page_config(page_title="Nexus", page_icon="icon.png", layout="wide")

    query_params = st.query_params

    # Get specific parameter values
    admin = query_params.get("admin", [None])[0]
    if not admin:
        st.write("Access this page through the Admin interface.")
        return

    win_height = st_js(js_expressions="top.innerHeight", key="SCR")
    if "log_messages" not in st.session_state:
        st.session_state.log_messages = ""

    if "last_log_message" not in st.session_state:
        st.session_state.last_log_message = None
    if username := st.session_state.get("username"):
        selected_page = st.sidebar.selectbox(
            "Nexus",
            [
                # "Agents Chat Playground",
                # "Assistants Chat Playground",
                "Actions",
                "Knowledge",
                "Memory",
                # "Profile",
                # "Usage",
                "Thought Templates",
                "Thought Trees",
                "Thought Networks",
                "Logout",
            ],
        )
        # if selected_page == "Agents":
        #     agent_page(username, win_height)
        #     return
        if selected_page == "Agents Chat Playground":
            chat_page(username, win_height)
            return
        elif selected_page == "Assistants Chat Playground":
            assistants_page(username, win_height)
            return
        elif selected_page == "Knowledge":
            knowledge_page(username, win_height)
            return
        elif selected_page == "Memory":
            memory_page(username, win_height)
            return
        elif selected_page == "Workflow":
            workflow_page(username, win_height)
            return
        elif selected_page == "Profile":
            profile_page(username, win_height)
            return
        elif selected_page == "Usage":
            usage_page(username, win_height)
            return
        elif selected_page == "Actions":
            actions_page(username, win_height)
            return
        elif selected_page == "Thought Templates":
            thought_templates_page(username, win_height)
            return
        elif selected_page == "Thought Trees":
            thought_templates_page(username, win_height)
            return
        elif selected_page == "Thought Networks":
            thought_templates_page(username, win_height)
            return
        elif selected_page == "Logout":
            st.session_state["username"] = None
            set_cookie("username", "", 0)
            time.sleep(5)
            st.rerun()
            return

    else:
        login_page()


if __name__ == "__main__":
    main()
