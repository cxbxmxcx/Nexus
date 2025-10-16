"""
Orchestration Status Component for Nexus Streamlit UI

⭐ ENHANCED AND STABILIZED VERSION - Replaces: nexus/streamlit_ui/orchestration_status.py
This version reads orchestration state directly from the agent instance for stability.
"""

import streamlit as st
from nexus.streamlit_ui.ui_helpers import display_orchestration_requirements_warning

class OrchestrationStatusUI:
    """UI component for displaying orchestration status."""

    def display_agent_health_dashboard(self, chat_agent):
        """Display a real-time health dashboard for the agent's sub-agents."""
        if not hasattr(chat_agent, 'profile') or not chat_agent.profile:
            st.warning("⚠️ No profile has been set for the current agent.")
            return

        if not hasattr(chat_agent.profile, 'orchestration') or not chat_agent.profile.orchestration:
            st.info("ℹ️ This agent profile is not configured for orchestration.")
            return

        with st.spinner("🔍 Loading orchestration dashboard..."):
            if not display_orchestration_requirements_warning():
                return

            # ⭐ CORRECTED: Get the manager directly from the agent instance.
            # This is the stable way to access the orchestration state.
            manager = getattr(chat_agent, 'orchestration_manager', None)

            st.subheader("🎭 Orchestration Dashboard")

            if not manager:
                st.info("🔄 Orchestration has not been initialized for this session.")
                if st.button("🚀 Initialize Agents Now"):
                    with st.spinner("🔄 Initializing agents..."):
                        try:
                            # Import action dynamically to avoid circular dependency issues
                            from nexus.nexus_base.nexus_actions.orchestration_actions import initialize_orchestration
                            agent_urls = chat_agent.profile.orchestration.get('agent_urls', '')
                            if agent_urls:
                                result = initialize_orchestration(agent_urls, _caller_agent=chat_agent)
                                st.success("Initialization request sent!")
                                st.info(result)
                                st.rerun() # Rerun to update the UI with the new state
                            else:
                                st.error("❌ No agent_urls are configured in the agent's profile.")
                        except Exception as e:
                            st.error(f"❌ Initialization failed: {e}")
                return

            cards = manager.get_all_agent_cards()
            if not cards:
                st.warning("⚠️ No sub-agents were loaded. Check the URLs in the profile and refresh.")
                return

            # --- Metrics Display ---
            active_count = len(manager.get_agents_by_status("active"))
            error_count = len(manager.get_agents_by_status("error"))
            total_count = len(cards)
            health_percentage = (active_count / total_count * 100) if total_count > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Sub-Agents", total_count)
            col2.metric("Active ✅", active_count, delta=active_count - (total_count - active_count - error_count))
            col3.metric("Errors ❌", error_count)
            st.progress(health_percentage / 100)

            # --- Agent List ---
            st.subheader("🤖 Sub-Agent Status")
            if st.button("🔄 Refresh All Agents"):
                with st.spinner("Refreshing all agents..."):
                    from nexus.nexus_base.nexus_actions.orchestration_actions import refresh_agents
                    st.info(refresh_agents(_caller_agent=chat_agent))
                    st.rerun()

            for card in cards:
                self._display_agent_card_ui(card)

    def _display_agent_card_ui(self, card):
        """Renders a single agent card with its status and details."""
        with st.container(border=True):
            col1, col2 = st.columns()
            with col1:
                if card.status == "active":
                    st.success("● Active", help="Agent is online and responding.")
                elif card.status == "error":
                    st.error("● Error", help=f"Error: {card.last_error}")
                else:
                    st.warning("● Inactive", help="Agent is offline or not responding.")

            with col2:
                st.markdown(f"**{card.name}**")
                st.caption(card.description)
                st.caption(f"URL: {card.url}")
                if card.status == "error":
                    st.error(f"Last Error: {card.last_error}", icon="🔥")
