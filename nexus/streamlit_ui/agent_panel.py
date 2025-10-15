import streamlit as st

from nexus.streamlit_ui.options import create_options_ui


def agent_panel(chat):
    st.title("Agent Settings")

    # Load agents
    agents = chat.get_agent_names()
    selected_agent = st.selectbox(
        "Choose an agent engine:",
        agents,
        key="agents",
        help="Choose an agent to chat with.",
    )

    # Get the agent object
    chat_agent = chat.get_agent(selected_agent)

    # Agent options (preserve behavior)
    with st.expander("Agent Options:", expanded=False):
        options = chat_agent.get_attribute_options()
        if options:
            selected_options = create_options_ui(options)
            for key, value in selected_options.items():
                setattr(chat_agent, key, value)

    # Determine A2A mode from sidebar toggle
    a2a_mode = st.session_state.get("a2a_mode", False)

    # Profiles selection: when in A2A mode show only orchestrator profiles, otherwise show regular profiles
    try:
        orchestrator_profiles = chat.profile_manager.get_orchestrator_profile_names()
    except Exception:
        # Fallback if the helper is not available
        orchestrator_profiles = []

    all_profiles = chat.get_profile_names()
    if a2a_mode:
        profiles = [p for p in all_profiles if p in orchestrator_profiles]
        mode_label = "🎭 Orchestrator"
    else:
        profiles = [p for p in all_profiles if p not in orchestrator_profiles]
        mode_label = "🤖 Agent"

    if not profiles:
        if a2a_mode:
            st.warning("⚠️ No orchestrator profiles found.")
            st.info("💡 Create a profile with an 'orchestration:' config section.")
        else:
            st.warning("⚠️ No agent profiles found.")
        return None

    def format_agent_profile(agent_name):
        profile = chat.get_profile(agent_name)
        return f"{profile.avatar} : {profile.name}"

    selected_profile = st.selectbox(
        f"Choose {mode_label} profile:",
        profiles,
        key="profiles",
        help=f"Choose a {'orchestrator' if a2a_mode else 'agent'} profile.",
        format_func=format_agent_profile,
    )

    # Configure discovered agent URLs and small discovery hint when orchestration profile selected
    if a2a_mode and selected_profile:
        profile = chat.get_profile(selected_profile)
        if hasattr(profile, "orchestration") and profile.orchestration:
            with st.expander("Orchestration info", expanded=False):
                agent_urls = profile.orchestration.get("agent_urls", "")
                st.text(f"Agent URLs: {agent_urls}")
                st.text(f"Timeout (s): {profile.orchestration.get('timeout_seconds', 30)}")

    # ------------------------- Actions handling ---------------------------
    # Goal: when in A2A mode, select orchestrator actions automatically (user shouldn't have to pick them).
    # When NOT in A2A mode, hide orchestrator-only actions.

    chat_agent.actions = []
    if chat_agent.supports_actions:
        # Load all action names from the system
        action_names = chat.get_action_names()

        # Try to get a list of actions that are considered orchestrator-only from the profile manager
        try:
            orchestrator_action_names = chat.profile_manager.get_orchestrator_action_names()
        except Exception:
            # If not present, common orchestrator action names (heuristic)
            orchestrator_action_names = ["orchestrate", "delegate_to_agent", "initialize_orchestration"]

        if a2a_mode:
            # Auto-select actions from selected profile if that profile provides an `actions` list
            try:
                profile_obj = chat.get_profile(selected_profile)
                profile_actions = getattr(profile_obj, "actions", None)
                if profile_actions:
                    # profile_actions expected to be a list of action names; convert to actual action objects
                    try:
                        selected_actions = chat.get_actions(profile_actions)
                    except Exception:
                        # Fall back to filtering action_names to those present in profile_actions
                        selected_actions = [a for a in action_names if a in profile_actions]
                    chat_agent.actions = selected_actions
                else:
                    # If profile doesn't list actions explicitly, try to default to orchestrator_action_names
                    try:
                        chat_agent.actions = chat.get_actions(orchestrator_action_names)
                    except Exception:
                        chat_agent.actions = [a for a in action_names if a in orchestrator_action_names]

                # Inform user which actions were auto-selected (small read-only note)
                st.caption(f"Auto-selected orchestrator actions: {', '.join(getattr(profile_obj, 'actions', orchestrator_action_names))}")

            except Exception as e:
                # Best-effort: if anything fails, fall back to empty actions and log a small note
                st.warning("Could not auto-select orchestrator actions: %s" % str(e))
                chat_agent.actions = []
        else:
            # Single-agent mode: hide orchestrator-only actions from the multiselect list
            filtered_action_names = [a for a in action_names if a not in orchestrator_action_names]

            selected_action_names = st.multiselect(
                "Select actions:",
                filtered_action_names,
                key="actions",
                help="Choose the actions the agent can use.",
            )
            try:
                selected_actions = chat.get_actions(selected_action_names)
            except Exception:
                # If chat.get_actions expects different input, fall back to storing names
                selected_actions = selected_action_names
            chat_agent.actions = selected_actions

    # Knowledge/memory stores (preserve original behavior)
    chat_agent.knowledge_store = "None"
    if chat_agent.supports_knowledge:
        knowledge_stores = chat.get_knowledge_store_names()
        selected_knowledge_store = st.selectbox(
            "Select a knowledge store:",
            ["None"] + knowledge_stores,
            key="knowledge_store",
            help="Choose the knowledge store to use.",
        )
        chat_agent.knowledge_store = selected_knowledge_store

    chat_agent.memory_store = "None"
    if chat_agent.supports_memory:
        memory_stores = chat.get_memory_store_names()
        selected_memory_store = st.selectbox(
            "Select a memory store:",
            ["None"] + memory_stores,
            key="memory_store",
            help="Choose the memory store to use.",
        )
        chat_agent.memory_store = selected_memory_store

    # Finally set the selected profile onto the agent object
    chat_agent.profile = chat.get_profile(selected_profile)

    return chat_agent
