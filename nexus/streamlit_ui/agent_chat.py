"""
Agent Chat for Nexus Streamlit UI with A2A Orchestration Mode

⭐ ENHANCED VERSION - Replace: nexus/streamlit_ui/agent_chat.py
"""

import streamlit as st

# ✅ ADDED: Import fallbacks
try:
    from streamlit_ui.agent_panel import agent_panel
    from streamlit_ui.chat_history import display_chat_history  
    from streamlit_ui.ui_helpers import get_nexus
except ImportError:
    try:
        from nexus.streamlit_ui.agent_panel import agent_panel
        from nexus.streamlit_ui.chat_history import display_chat_history
        from nexus.streamlit_ui.ui_helpers import get_nexus
    except ImportError:
        from .agent_panel import agent_panel
        from .chat_history import display_chat_history
        from .ui_helpers import get_nexus


def chat_page(username, win_height):
    """Main chat page with A2A orchestration support and loading states."""

    # ✅ ADDED: Loading state for Nexus initialization
    with st.spinner("🔄 Initializing Nexus..."):
        chat = get_nexus()
        user = chat.get_participant(username)

    if user is None:
        st.error("❌ Invalid user")
        st.stop()

    # Initialize session state
    if "a2a_mode" not in st.session_state:
        st.session_state["a2a_mode"] = False

    if "current_thread_id" not in st.session_state:
        st.session_state["current_thread_id"] = None

    # Layout
    col1, col2 = st.columns([1, 2], gap="medium")

    with col1:
        st.title("Nexus -> Agents")

        # A2A Toggle with loading feedback
        a2a_mode = st.toggle(
            "🎭 A2A Orchestration Mode",
            value=st.session_state["a2a_mode"],
            help="Enable to use orchestrator profiles that coordinate multiple A2A agents",
            key="a2a_mode"
        )

        # ✅ ADDED: Better mode info with loading states
        if a2a_mode:
            # Check orchestration requirements
            with st.spinner("🔍 Checking A2A requirements..."):
                try:
                    from nexus.streamlit_ui.ui_helpers import check_orchestration_requirements
                    missing = check_orchestration_requirements()
                    if missing:
                        st.error("❌ Missing A2A requirements")
                        for req in missing:
                            st.code(f"pip install {req}")
                        st.stop()
                    else:
                        st.success("🎭 **Orchestration Mode Active**")
                        st.info("Orchestrator profiles coordinate multiple A2A sub-agents to handle complex tasks.")
                except Exception as e:
                    st.warning(f"⚠️ Could not verify A2A requirements: {e}")
                    st.info("🎭 **Orchestration Mode Active** (requirements not verified)")
        else:
            st.info("🤖 **Standard Agent Mode**\n\nDirect interaction with individual agent profiles.")

        # ✅ ADDED: Loading state for agent panel
        with st.spinner("🔄 Loading agent profiles..."):
            chat_agent = agent_panel(chat)

        if chat_agent is None:
            st.stop()

        # Store current agent in session state
        st.session_state["current_chat_agent"] = chat_agent

    with col2:
        st.title(f"Chat with {chat_agent.profile.avatar} {chat_agent.profile.name}")

        # Show orchestration status if in A2A mode
        if a2a_mode and hasattr(chat_agent.profile, 'orchestration') and chat_agent.profile.orchestration:
            orchestration_config = chat_agent.profile.orchestration

            with st.expander("🎭 Orchestration Configuration", expanded=False):
                col_a, col_b = st.columns(2)

                with col_a:
                    st.metric("Max Depth", orchestration_config.get('max_delegation_depth', 3))
                    st.metric("Timeout (sec)", orchestration_config.get('timeout_seconds', 30))

                with col_b:
                    auto_init = orchestration_config.get('auto_initialize', False)
                    st.metric("Auto Initialize", "✅" if auto_init else "❌")
                    agent_urls = orchestration_config.get('agent_urls', '')
                    agent_count = len([u for u in agent_urls.split(',') if u.strip()])
                    st.metric("Configured Agents", agent_count)

                # ✅ ADDED: Real-time orchestration status
                if st.button("🔄 Refresh Status"):
                    with st.spinner("🔍 Checking orchestration status..."):
                        try:
                            from nexus.nexus_base.nexus_actions.orchestration_actions import get_orchestration_status
                            status = get_orchestration_status(_caller_agent=chat_agent)
                            st.success("Status updated!")
                            st.info(status)
                        except Exception as e:
                            st.error(f"Status check failed: {e}")

        # Get or create thread with loading
        thread_id = st.session_state.get("current_thread_id")
        if not thread_id:
            with st.spinner("🔄 Creating chat thread..."):
                thread = chat.create_thread(
                    f"Chat_{username}_{chat_agent.profile.name}",
                    username,
                    type="agent"
                )
                thread_id = thread.thread_id
                st.session_state["current_thread_id"] = thread_id

        # ✅ ADDED: Loading state for chat history
        with st.spinner("📚 Loading chat history..."):
            messages = chat.read_messages(thread_id)

        # Display messages
        for message in messages:
            with st.chat_message(message.role):
                st.markdown(message.content)

        # Chat input
        user_input = st.chat_input(
            f"Message {chat_agent.profile.name}..." if not a2a_mode
            else f"Give orchestration task to {chat_agent.profile.name}...",
            key="chat_input"
        )

        if user_input:
            # Add user message
            chat.post_message(thread_id, username, "user", user_input)

            # Display user message
            with st.chat_message("user"):
                st.markdown(user_input)

            # ✅ ENHANCED: Better loading states for responses
            with st.chat_message("assistant"):
                if a2a_mode:
                    with st.spinner("🎭 Orchestrating across multiple agents..."):
                        # Show additional status for orchestration
                        status_placeholder = st.empty()
                        status_placeholder.info("🔍 Analyzing task and selecting agents...")

                        response_generator = chat_agent.get_response_stream(user_input, thread_id)

                        status_placeholder.info("🤝 Delegating to sub-agents...")
                else:
                    with st.spinner(f"💭 {chat_agent.profile.name} is thinking..."):
                        response_generator = chat_agent.get_response_stream(user_input, thread_id)

                # Process streaming response with loading feedback
                if hasattr(response_generator, '__call__'):
                    response_func = response_generator()
                    full_response = ""
                    message_placeholder = st.empty()

                    # ✅ ADDED: Progress indicator for streaming
                    progress_placeholder = st.empty()
                    char_count = 0

                    for chunk in response_func:
                        full_response += chunk
                        char_count += len(chunk)

                        # Update response
                        message_placeholder.markdown(full_response + "▌")

                        # Update progress (every 50 characters)
                        if char_count % 50 == 0:
                            progress_placeholder.caption(f"📝 Received {char_count} characters...")

                    # Clear progress and finalize
                    progress_placeholder.empty()
                    message_placeholder.markdown(full_response)
                else:
                    full_response = str(response_generator)
                    st.markdown(full_response)

                # Clear orchestration status if it was shown
                if a2a_mode and 'status_placeholder' in locals():
                    status_placeholder.empty()

                # Add assistant response to thread
                chat.post_message(thread_id, chat_agent.profile.name, "assistant", full_response)

            # ✅ ADDED: Success feedback
            if a2a_mode:
                st.success("✅ Orchestration completed!")

            # Refresh to show new messages
            st.rerun()


def main():
    """Entry point for the chat application."""
    if "username" not in st.session_state:
        st.session_state["username"] = "default_user"

    chat_page(st.session_state["username"], win_height=600)


if __name__ == "__main__":
    main()
