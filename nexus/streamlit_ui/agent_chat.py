# File: nexus/streamlit_ui/agent_chat.py (UPDATED)
# Purpose: Restore previous chat UI/threads behavior while adding a single A2A toggle
# and minimal orchestration config display. Uses existing chat threading UI.

import streamlit as st

from nexus.streamlit_ui.agent_panel import agent_panel
from nexus.streamlit_ui.cache import get_nexus


def chat_page(username, win_height):
    """Chat page that preserves the original thread/sidebar UX and adds a single
    toggle for A2A orchestration mode and a small orchestration config expander.

    Behavior changes made to satisfy request:
    - Keep the "Recent chats" sidebar with chat numbers (previous design preserved).
    - Add one toggle (sidebar) to enable/disable A2A orchestration globally for the session.
    - Show a minimal orchestrator config box when A2A mode is enabled (read-only, from profile).
    - Use agent_panel(chat) to choose agent/profile; agent_panel will automatically
      pre-select orchestrator actions when A2A mode is enabled.
    """

    chat = get_nexus()
    user = chat.get_participant(username)
    if user is None:
        st.error("Invalid user")
        st.stop()

    # Session state initialization
    if "threads" not in st.session_state:
        st.session_state["threads"] = chat.get_threads_for_user(username)
    if "current_thread_id" not in st.session_state:
        st.session_state["current_thread_id"] = None
    if "a2a_mode" not in st.session_state:
        st.session_state["a2a_mode"] = False

    def select_thread(thread_id):
        st.session_state["current_thread_id"] = thread_id
        # keep the old behavior of setting agent to None for the thread (so agent_panel can set it)
        for thread in st.session_state["threads"]:
            if thread.thread_id == thread_id:
                thread.agent = None
                break

    def create_new_thread():
        new_thread_id = (
            len(st.session_state["threads"]) + 1 if st.session_state["threads"] else 1
        )
        thread = chat.create_thread(f"Chat: {new_thread_id}", username)
        st.session_state["threads"].insert(0, thread)
        select_thread(thread.thread_id)

    # Sidebar keeps the old threads UI and adds toggle + orchestrator config
    st.sidebar.title("Nexus -> Agents")
    with st.sidebar.container(height=win_height - 300):
        st.button("+ New Chat", on_click=create_new_thread)

        # A2A Toggle (single switch requested)
        st.session_state["a2a_mode"] = st.checkbox(
            "🎭 A2A Orchestration Mode",
            value=st.session_state.get("a2a_mode", False),
            help="Enable to use orchestrator profiles that coordinate multiple agents",
            key="a2a_mode_checkbox",
        )

        # Orchestration config quick view (only visible when A2A mode enabled)
        if st.session_state["a2a_mode"]:
            with st.expander("Orchestrator Config", expanded=False):
                # Attempt to display orchestration config from currently selected profile (if any)
                try:
                    # If a thread is selected and has an agent, use it; otherwise skip
                    if st.session_state.get("current_thread_id"):
                        t = chat.get_thread(st.session_state["current_thread_id"])
                        # thread.agent may be None; fall back to last selected agent in session
                    # Use a best-effort lookup for profile info; not failing hard if unavailable
                    profile = None
                    if "last_selected_profile" in st.session_state:
                        profile = chat.get_profile(st.session_state["last_selected_profile"])
                    if profile and hasattr(profile, "orchestration") and profile.orchestration:
                        cfg = profile.orchestration
                        st.text(f"Agent URLs: {cfg.get('agent_urls', '')}")
                        st.text(f"Timeout (s): {cfg.get('timeout_seconds', 30)}")
                        st.text(f"Max depth: {cfg.get('max_delegation_depth', 3)}")
                        st.text(f"Auto init: {cfg.get('auto_initialize', False)}")
                    else:
                        st.info("No orchestrator profile selected. Select an orchestrator profile in Agent Settings.")
                except Exception:
                    st.info("Orchestrator config not available")

        st.header("Recent chats")
        for thread in st.session_state["threads"]:
            # Keep numeric/chat title behavior from previous design
            if st.button(thread.title, key=f"thread_{thread.thread_id}"):
                select_thread(thread.thread_id)

    # Main chat UI
    if st.session_state["current_thread_id"] is not None:
        current_thread = chat.get_thread(st.session_state["current_thread_id"]) if st.session_state["current_thread_id"] else None
        if current_thread:
            with st.container():
                col_chat, col_agent = st.columns([4, 2])

                with col_chat:
                    st.title(current_thread.title)
                    with st.container():
                        messages = chat.read_messages(current_thread.thread_id)
                        for message in messages:
                            # original code displayed avatar and used author; preserve that
                            author_avatar = getattr(message.author, "avatar", None)
                            with st.chat_message(message.author.username, avatar=author_avatar):
                                st.markdown(message.content)

                        placeholder = st.empty()

                    user_input = st.chat_input("Type your message here:", key="msg_input")

                with col_agent:
                    # agent_panel now respects a2a_mode and will pre-select orchestrator actions when appropriate
                    chat_agent = agent_panel(chat)

                # keep history association so the agent can access it if needed
                chat_agent.chat_history = messages

                # cache last selected profile used by sidebar config view
                try:
                    if chat_agent and chat_agent.profile and hasattr(chat_agent.profile, "name"):
                        st.session_state["last_selected_profile"] = chat_agent.profile.name
                except Exception:
                    pass

                if user_input:
                    with placeholder.container():
                        with st.chat_message(username, avatar=user.avatar):
                            st.markdown(user_input)
                            chat.post_message(
                                current_thread.thread_id, username, "user", user_input
                            )

                        with st.chat_message(chat_agent.name, avatar=getattr(chat_agent.profile, "avatar", None)):
                            with st.spinner(text="The agent is thinking..."):
                                # Keep existing tracking, RAG and streaming behavior
                                try:
                                    chat.set_tracking_id(f"chat:thread{current_thread.thread_id}:{username}")
                                except Exception:
                                    pass

                                knowledge_rag = ""
                                try:
                                    if getattr(chat_agent, "knowledge_store", None) and chat_agent.knowledge_store != "None":
                                        knowledge_rag = chat.apply_knowledge_RAG(
                                            chat_agent.knowledge_store, user_input
                                        )
                                except Exception:
                                    knowledge_rag = ""

                                memory_rag = ""
                                try:
                                    if getattr(chat_agent, "memory_store", None) and chat_agent.memory_store != "None":
                                        memory_rag = chat.apply_memory_RAG(
                                            chat_agent.memory_store, user_input, chat_agent
                                        )
                                except Exception:
                                    memory_rag = ""

                                content = user_input + knowledge_rag + memory_rag

                                # If A2A mode is enabled and the profile supports orchestration, let the profile handle orchestration
                                try:
                                    if st.session_state.get("a2a_mode") and hasattr(chat_agent.profile, "orchestration") and chat_agent.profile.orchestration:
                                        # rely on agent's get_response_stream to perform orchestration
                                        st.write_stream(chat_agent.get_response_stream(content, current_thread.thread_id))
                                    else:
                                        st.write_stream(chat_agent.get_response_stream(content, current_thread.thread_id))
                                finally:
                                    # post-processing similar to old flow
                                    if getattr(chat_agent, "memory_store", None) and chat_agent.memory_store != "None":
                                        try:
                                            chat.append_memory(
                                                chat_agent.memory_store,
                                                user_input,
                                                chat_agent.last_message,
                                                chat_agent,
                                            )
                                        except Exception:
                                            pass
                                    try:
                                        chat.set_tracking_id("Not set")
                                    except Exception:
                                        pass
                                    try:
                                        chat.post_message(
                                            current_thread.thread_id,
                                            chat_agent.name,
                                            "agent",
                                            getattr(chat_agent, "last_message", ""),
                                        )
                                    except Exception:
                                        pass

                    st.rerun()


def main():
    if "username" not in st.session_state:
        st.session_state["username"] = "default_user"

    chat_page(st.session_state["username"], win_height=600)


if __name__ == "__main__":
    main()
