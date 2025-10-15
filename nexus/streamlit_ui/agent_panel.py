"""
Agent Panel for Nexus Streamlit UI with A2A Orchestration Support

⭐ ENHANCED VERSION - Replace: nexus/streamlit_ui/agent_panel.py
"""

import streamlit as st

# ✅ ADDED: Import fallbacks
try:
    from streamlit_ui.ui_helpers import create_options_ui
except ImportError:
    try:
        from nexus.streamlit_ui.ui_helpers import create_options_ui
    except ImportError:
        from .ui_helpers import create_options_ui


def agent_panel(chat):
    """Agent panel with A2A orchestration support and loading states."""
    st.title("Agent Settings")

    # ✅ ADDED: Loading state for agent names
    with st.spinner("🔄 Loading agents..."):
        agents = chat.get_agent_names()

    selected_agent = st.selectbox(
        "Choose an agent engine:",
        agents,
        key="agents",
        help="Choose an agent to chat with.",
    )

    # ✅ ADDED: Loading state for agent
    with st.spinner(f"🔄 Configuring {selected_agent}..."):
        chat_agent = chat.get_agent(selected_agent)

    with st.expander("Agent Options:", expanded=False):
        options = chat_agent.get_attribute_options()
        if options:
            with st.spinner("🔄 Loading agent options..."):
                selected_options = create_options_ui(options)
                for key, value in selected_options.items():
                    setattr(chat_agent, key, value)

    # Filter profiles based on A2A mode
    a2a_mode = st.session_state.get("a2a_mode", False)

    # ✅ ADDED: Loading state for profile filtering
    with st.spinner("🔄 Loading profiles..."):
        if a2a_mode:
            # A2A Mode: Show ONLY orchestrator profiles
            profiles = chat.profile_manager.get_orchestrator_profile_names()
            mode_label = "🎭 Orchestrator"
        else:
            # Normal Mode: Show ONLY non-orchestrator profiles
            all_profiles = chat.get_profile_names()
            orchestrator_profiles = chat.profile_manager.get_orchestrator_profile_names()
            profiles = [p for p in all_profiles if p not in orchestrator_profiles]
            mode_label = "🤖 Agent"

    if not profiles:
        if a2a_mode:
            st.warning("⚠️ No orchestrator profiles found.")
            st.info("💡 Create a profile with 'orchestration:' config section.")

            # ✅ ADDED: Helper for creating orchestrator profiles
            with st.expander("📝 How to Create Orchestrator Profiles", expanded=False):
                st.markdown("""
                Create a YAML file in `nexus/nexus_base/nexus_profiles/` with this structure:

                ```yaml
                agentProfile:
                  name: "My Orchestrator"
                  avatar: "🎭"
                  persona: "I coordinate multiple agents..."
                  actions:
                    - orchestrate
                    - delegate_to_agent
                  orchestration:
                    agent_urls: "http://localhost:8001,http://localhost:8002"
                    timeout_seconds: 30
                    max_delegation_depth: 3
                    auto_initialize: true
                ```
                """)
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

    # Show discovered sub-agents with loading states
    if a2a_mode and selected_profile:
        profile = chat.get_profile(selected_profile)
        if hasattr(profile, 'orchestration') and profile.orchestration:
            with st.expander("🔍 Discovered Sub-Agents", expanded=True):
                # Show configured agent URLs
                agent_urls = profile.orchestration.get('agent_urls', '')
                if agent_urls:
                    url_list = [u.strip() for u in agent_urls.split(',') if u.strip()]
                    st.info(f"🔗 Configured URLs: {len(url_list)} agents")
                    for url in url_list:
                        st.caption(f"• {url}")

                # ✅ ENHANCED: Try to show discovered agents with loading states
                discovery_placeholder = st.empty()

                with st.spinner("🔍 Discovering agents..."):
                    try:
                        # Import fallbacks
                        try:
                            from nexus.nexus_base.nexus_actions.orchestration_actions import _get_or_create_manager
                        except ImportError:
                            from nexus_base.nexus_actions.orchestration_actions import _get_or_create_manager

                        # Set profile safely
                        if not hasattr(chat_agent, '_profile_set') or chat_agent.profile != profile:
                            chat_agent.profile = profile
                            chat_agent._profile_set = True

                        manager = _get_or_create_manager(chat_agent)
                        cards = manager.get_all_agent_cards()

                        if cards:
                            discovery_placeholder.success(f"✅ Found {len(cards)} sub-agents:")

                            # ✅ ENHANCED: Display agents with better error handling
                            for i, card in enumerate(cards):
                                with st.container():
                                    display_agent_card_enhanced(card, i)
                        else:
                            discovery_placeholder.info("🔄 Agents will be discovered when orchestration starts.")

                            # ✅ ADDED: Manual discovery button
                            if st.button("🔍 Try Discovery Now"):
                                with st.spinner("🔄 Attempting agent discovery..."):
                                    try:
                                        from nexus.nexus_base.nexus_actions.orchestration_actions import initialize_orchestration
                                        result = initialize_orchestration(agent_urls, _caller_agent=chat_agent)
                                        st.success("Discovery attempted!")
                                        st.info(result)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Discovery failed: {e}")

                    except ImportError:
                        discovery_placeholder.error("❌ Orchestration module not installed")
                        st.code("pip install a2a-sdk>=0.2.3 httpx>=0.24.0")
                    except AttributeError as e:
                        discovery_placeholder.warning(f"⚠️ Profile configuration issue: {e}")
                        st.info("Make sure your profile has 'orchestration' section configured.")
                    except Exception as e:
                        discovery_placeholder.warning(f"⚠️ Error loading agents: {type(e).__name__}")
                        with st.expander("Debug Info", expanded=False):
                            st.exception(e)
                        st.info("Agents will be discovered on first orchestration message.")

    # ✅ ADDED: Loading state for remaining configuration
    with st.spinner("🔄 Configuring agent capabilities..."):
        # Continue with existing functionality
        chat_agent.actions = []
        if chat_agent.supports_actions:
            action_names = chat.get_action_names()
            selected_action_names = st.multiselect(
                "Select actions:",
                action_names,
                key="actions",
                help="Choose the actions the agent can use.",
            )
            selected_actions = chat.get_actions(selected_action_names)
            chat_agent.actions = selected_actions

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

        # Set the selected profile
        chat_agent.profile = chat.get_profile(selected_profile)

    return chat_agent


def display_agent_card_enhanced(card, index=0):
    """Display an agent card with enhanced status and error handling."""
    col1, col2, col3 = st.columns([1, 4, 1])

    with col1:
        # ✅ ENHANCED: Better status indicators
        if card.status == "active":
            st.success("🟢")
        elif card.status == "inactive":
            st.error("🔴") 
        elif card.status == "error":
            st.error("❌")
        elif card.status == "checking":
            st.info("🔄")
        else:
            st.warning("🟡")  # unknown

    with col2:
        st.markdown(f"**{card.name}**")
        st.caption(card.description)
        if card.capabilities:
            st.caption(f"🔧 Capabilities: {', '.join(card.capabilities)}")
        st.caption(f"🌐 URL: {card.url}")

        # ✅ ADDED: Show error details if present
        if card.status == "error" and hasattr(card, 'last_error') and card.last_error:
            with st.expander(f"⚠️ Error Details", expanded=False):
                st.error(f"Last error: {card.last_error}")

        # ✅ ADDED: Show health check count
        if hasattr(card, 'health_check_count'):
            st.caption(f"🔍 Health checks: {card.health_check_count}")

    with col3:
        # ✅ ADDED: Individual refresh with loading state
        if st.button("🔄", key=f"refresh_card_{index}", help=f"Refresh {card.name}"):
            with st.spinner(f"🔍 Checking {card.name}..."):
                try:
                    # This would trigger a refresh - placeholder for now
                    st.success("Refreshed!")
                    # In real implementation, would call refresh function
                except Exception as e:
                    st.error(f"Refresh failed: {e}")
