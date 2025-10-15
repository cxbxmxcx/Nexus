"""
Orchestration Status Component for Nexus Streamlit UI

⭐ ENHANCED VERSION - Replace: nexus/streamlit_ui/orchestration_status.py
"""

import streamlit as st
import asyncio
from typing import Optional, Dict, List

# ✅ ADDED: Import fallbacks
try:
    from streamlit_ui.ui_helpers import check_orchestration_requirements, display_orchestration_requirements_warning
except ImportError:
    try:
        from nexus.streamlit_ui.ui_helpers import check_orchestration_requirements, display_orchestration_requirements_warning
    except ImportError:
        from .ui_helpers import check_orchestration_requirements, display_orchestration_requirements_warning


class OrchestrationStatusUI:
    """UI component for displaying orchestration status with enhancements."""

    def __init__(self):
        self.manager = None

    def display_agent_health_dashboard(self, chat_agent):
        """Display real-time agent health dashboard with loading states."""
        if not hasattr(chat_agent, 'profile') or not chat_agent.profile:
            st.warning("⚠️ No profile set for agent")
            return

        if not hasattr(chat_agent.profile, 'orchestration') or not chat_agent.profile.orchestration:
            st.info("ℹ️ This agent is not configured for orchestration")
            return

        # ✅ ENHANCED: Better loading and requirements check
        with st.spinner("🔍 Loading orchestration dashboard..."):
            try:
                # Check requirements first
                if not display_orchestration_requirements_warning():
                    return

                # Import fallbacks
                try:
                    from nexus.nexus_base.nexus_actions.orchestration_actions import _get_or_create_manager
                except ImportError:
                    from nexus_base.nexus_actions.orchestration_actions import _get_or_create_manager

                manager = _get_or_create_manager(chat_agent)

                st.subheader("🎭 Orchestration Dashboard")

                # Overall health metrics
                cards = manager.get_all_agent_cards()
                if not cards:
                    st.info("🔄 No agents discovered yet. Start a conversation to initialize.")

                    # ✅ ADDED: Manual initialization button
                    if st.button("🚀 Initialize Agents Now"):
                        with st.spinner("🔄 Initializing orchestration..."):
                            try:
                                from nexus.nexus_base.nexus_actions.orchestration_actions import initialize_orchestration
                                agent_urls = chat_agent.profile.orchestration.get('agent_urls', '')
                                result = initialize_orchestration(agent_urls, _caller_agent=chat_agent)
                                st.success("Initialization attempted!")
                                st.info(result)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Initialization failed: {e}")
                    return

                # ✅ ENHANCED: Better metrics display with loading
                with st.spinner("📊 Calculating agent metrics..."):
                    active_count = sum(1 for card in cards if card.status == "active")
                    inactive_count = sum(1 for card in cards if card.status == "inactive")
                    error_count = sum(1 for card in cards if card.status == "error")
                    unknown_count = sum(1 for card in cards if card.status == "unknown")
                    total_count = len(cards)
                    health_percentage = (active_count / total_count * 100) if total_count > 0 else 0

                # Metrics display
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Total", total_count)
                with col2:
                    st.metric("Active", active_count, delta=active_count-inactive_count)
                with col3:
                    st.metric("Inactive", inactive_count)
                with col4:
                    st.metric("Errors", error_count)
                with col5:
                    st.metric("Health %", f"{health_percentage:.0f}%")

                # Individual agent status with loading
                st.subheader("🤖 Sub-Agent Status")

                # ✅ ADDED: Batch refresh button
                col_refresh, col_status = st.columns([2, 1])
                with col_refresh:
                    if st.button("🔄 Refresh All Agents"):
                        with st.spinner("🔄 Refreshing all agents..."):
                            try:
                                from nexus.nexus_base.nexus_actions.orchestration_actions import refresh_agents
                                result = refresh_agents(_caller_agent=chat_agent)
                                st.success("All agents refreshed!")
                                st.info(result)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Batch refresh failed: {e}")

                with col_status:
                    if st.button("📊 Get Status"):
                        with st.spinner("📊 Getting status..."):
                            try:
                                from nexus.nexus_base.nexus_actions.orchestration_actions import get_orchestration_status
                                status = get_orchestration_status(_caller_agent=chat_agent)
                                st.success("Status retrieved!")
                                st.info(status)
                            except Exception as e:
                                st.error(f"Status failed: {e}")

                # Display individual agents
                for i, card in enumerate(cards):
                    self._display_agent_card_with_actions(card, manager, i)

            except ImportError as e:
                st.error("❌ Orchestration components not available")
                st.code(f"pip install a2a-sdk>=0.2.3 httpx>=0.24.0")
            except Exception as e:
                st.error(f"❌ Error loading orchestration status")
                with st.expander("Debug Details"):
                    st.exception(e)

    def _display_agent_card_with_actions(self, card, manager, index):
        """Display agent card with enhanced actions and loading."""
        with st.container():
            col1, col2, col3 = st.columns([1, 4, 1])

            with col1:
                # ✅ ENHANCED: Better status indicators with tooltips
                if card.status == "active":
                    st.success("🟢", help="Agent is online and responding")
                elif card.status == "inactive":
                    st.error("🔴", help="Agent is offline or not responding") 
                elif card.status == "error":
                    st.error("❌", help="Agent has errors")
                elif card.status == "checking":
                    st.info("🔄", help="Health check in progress")
                else:
                    st.warning("🟡", help="Status unknown")

            with col2:
                st.markdown(f"**{card.name}**")
                st.caption(card.description)
                if card.capabilities:
                    st.caption(f"🔧 Capabilities: {', '.join(card.capabilities)}")
                st.caption(f"🌐 URL: {card.url}")

                # ✅ ENHANCED: Show detailed status info
                if hasattr(card, 'last_error') and card.last_error:
                    with st.expander(f"⚠️ Error Details", expanded=False):
                        st.error(f"Last error: {card.last_error}")

                if hasattr(card, 'health_check_count'):
                    st.caption(f"🔍 Health checks: {card.health_check_count}")

            with col3:
                # ✅ ENHANCED: Individual refresh with better loading
                if st.button("🔄", key=f"refresh_card_{index}", help=f"Refresh {card.name}"):
                    with st.spinner(f"🔍 Checking {card.name}..."):
                        try:
                            # Safe refresh using _run_coro if available
                            new_status = self._refresh_agent_status(manager, card)
                            if new_status:
                                st.success(f"Status: {new_status}")
                                if new_status != card.status:
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Refresh failed: {str(e)}")

    def _refresh_agent_status(self, manager, card):
        """Refresh single agent status safely with enhanced error handling."""
        try:
            # ✅ USING: Enhanced async execution
            from nexus.nexus_base.nexus_actions.orchestration_actions import _run_coro

            async def check_health():
                return await manager._check_agent_health_with_fallback(card.url)

            new_status = _run_coro(check_health())
            card.status = new_status
            return new_status
        except Exception as e:
            if hasattr(card, 'mark_error'):
                card.mark_error(e)
            else:
                card.status = "error"
            return "error"

    def display_orchestration_logs(self, chat_agent):
        """Display orchestration execution logs with enhancements."""
        st.subheader("📋 Orchestration Logs")

        # ✅ ENHANCED: Better log management
        if "orchestration_logs" not in st.session_state:
            st.session_state.orchestration_logs = []

        # Log controls
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🔄 Refresh Logs"):
                with st.spinner("🔄 Loading latest logs..."):
                    # In real implementation, would fetch from logging system
                    st.success("Logs refreshed!")

        with col2:
            if st.button("🗑️ Clear Logs") and st.session_state.orchestration_logs:
                st.session_state.orchestration_logs = []
                st.success("Logs cleared!")
                st.rerun()

        # Display logs
        logs = st.session_state.orchestration_logs
        if logs:
            # Show in reverse order (newest first) with loading
            with st.spinner("📋 Loading logs..."):
                for i, log in enumerate(reversed(logs[-20:])):  # Last 20 logs
                    with st.expander(f"Log {len(logs)-i}: {log.get('timestamp', 'Unknown time')}", expanded=False):
                        st.json(log)
        else:
            st.info("No orchestration logs yet. Logs will appear when orchestration tasks are executed.")


def display_orchestration_sidebar(chat_agent):
    """Display enhanced orchestration controls in sidebar."""
    if not hasattr(chat_agent, 'profile') or not chat_agent.profile:
        return

    if not hasattr(chat_agent.profile, 'orchestration') or not chat_agent.profile.orchestration:
        return

    st.sidebar.subheader("🎭 Orchestration Controls")

    # ✅ ENHANCED: Better action handling with loading states
    if st.sidebar.button("🔄 Refresh All Agents"):
        with st.sidebar:
            with st.spinner("🔄 Refreshing..."):
                try:
                    from nexus.nexus_base.nexus_actions.orchestration_actions import refresh_agents
                    result = refresh_agents(_caller_agent=chat_agent)
                    st.success("✅ Refreshed!")
                    st.info(result)
                except ImportError:
                    st.error("❌ Actions not available")
                except Exception as e:
                    st.error(f"❌ Failed: {str(e)}")

    if st.sidebar.button("📊 Get Status"):
        with st.sidebar:
            with st.spinner("📊 Checking..."):
                try:
                    from nexus.nexus_base.nexus_actions.orchestration_actions import get_orchestration_status
                    status = get_orchestration_status(_caller_agent=chat_agent)
                    st.info(status)
                except ImportError:
                    st.error("❌ Actions not available")
                except Exception as e:
                    st.error(f"❌ Failed: {str(e)}")

    if st.sidebar.button("🧹 Cleanup Resources"):
        with st.sidebar:
            with st.spinner("🧹 Cleaning..."):
                try:
                    from nexus.nexus_base.nexus_actions.orchestration_actions import cleanup_orchestration
                    result = cleanup_orchestration(_caller_agent=chat_agent)
                    st.success(result)
                except Exception as e:
                    st.error(f"❌ Failed: {str(e)}")

    # ✅ ENHANCED: Configuration display with better formatting
    st.sidebar.markdown("**Configuration:**")
    config = chat_agent.profile.orchestration
    agent_urls = config.get('agent_urls', '')
    url_count = len([u for u in agent_urls.split(',') if u.strip()])

    st.sidebar.markdown(f"🔗 Agent URLs: `{url_count}`")
    st.sidebar.markdown(f"⏱️ Timeout: `{config.get('timeout_seconds', 30)}s`")
    st.sidebar.markdown(f"📊 Max Depth: `{config.get('max_delegation_depth', 3)}`")
    st.sidebar.markdown(f"🔄 Auto Init: `{config.get('auto_initialize', False)}`")

    # ✅ ADDED: Show URLs in expandable section
    with st.sidebar.expander("🔗 Agent URLs", expanded=False):
        urls = [u.strip() for u in agent_urls.split(',') if u.strip()]
        for i, url in enumerate(urls, 1):
            st.markdown(f"**{i}.** {url}")
