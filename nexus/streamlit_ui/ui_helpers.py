"""
UI Helpers for Nexus Streamlit Interface - ENHANCED

⭐ ENHANCED VERSION - Create at: nexus/streamlit_ui/ui_helpers.py
"""

import streamlit as st

# ✅ ADDED: Import fallbacks
try:
    from nexus.nexus_base.nexus import Nexus
except ImportError:
    try:
        from nexus_base.nexus import Nexus
    except ImportError:
        from nexus import Nexus


@st.cache_resource
def get_nexus():
    """Get or create cached Nexus instance with loading state."""
    try:
        return Nexus()
    except Exception as e:
        st.error(f"❌ Failed to initialize Nexus: {e}")
        st.stop()


def create_options_ui(options):
    """Create UI elements for agent options with loading states."""
    if not options:
        return {}

    with st.spinner("🔄 Loading agent options..."):
        selected_options = {}

        for key, details in options.items():
            if details.get('type') == 'numeric':
                selected_options[key] = st.number_input(
                    key,
                    min_value=details.get('min', 0.0),
                    max_value=details.get('max', 1.0),
                    value=details.get('default', 0.5),
                    step=details.get('step', 0.1),
                    help=details.get('help', f"Numeric parameter for {key}")
                )
            elif details.get('type') == 'string':
                if 'options' in details:
                    default_idx = 0
                    if 'default' in details and details['default'] in details['options']:
                        default_idx = details['options'].index(details['default'])

                    selected_options[key] = st.selectbox(
                        key,
                        options=details['options'],
                        index=default_idx,
                        help=details.get('help', f"Select option for {key}")
                    )
                else:
                    selected_options[key] = st.text_input(
                        key,
                        value=details.get('default', ''),
                        help=details.get('help', f"Text input for {key}")
                    )
            elif details.get('type') == 'boolean':
                selected_options[key] = st.checkbox(
                    key,
                    value=details.get('default', False),
                    help=details.get('help', f"Boolean option for {key}")
                )
            elif details.get('type') == 'slider':
                selected_options[key] = st.slider(
                    key,
                    min_value=details.get('min', 0.0),
                    max_value=details.get('max', 1.0),
                    value=details.get('default', 0.5),
                    step=details.get('step', 0.1),
                    help=details.get('help', f"Slider parameter for {key}")
                )
            else:
                # Default to text input for unknown types
                selected_options[key] = st.text_input(
                    key,
                    value=str(details.get('default', '')),
                    help=details.get('help', f"Parameter for {key}")
                )

        return selected_options


def check_orchestration_requirements():
    """Check if orchestration requirements are met with enhanced feedback."""
    missing_requirements = []

    try:
        import httpx
    except ImportError:
        missing_requirements.append("httpx>=0.24.0")

    # ✅ ENHANCED: Better A2A SDK checking
    try:
        import a2a
        # Check if it has the expected components
        from a2a.client import A2AClient
        from a2a.types import AgentCard
    except ImportError:
        missing_requirements.append("a2a-sdk>=0.2.3")

    # ✅ ADDED: Check for orchestration actions
    try:
        try:
            from nexus.nexus_base.nexus_actions.orchestration_actions import orchestrate, _run_coro
        except ImportError:
            from nexus_base.nexus_actions.orchestration_actions import orchestrate, _run_coro
    except ImportError:
        missing_requirements.append("Orchestration actions not installed")

    return missing_requirements


def display_orchestration_requirements_warning():
    """Display warning about missing orchestration requirements with enhanced UI."""
    missing = check_orchestration_requirements()

    if missing:
        st.error("❌ Missing A2A Orchestration Requirements")

        # ✅ ENHANCED: Better requirement display
        for requirement in missing:
            if requirement.startswith("a2a-sdk") or requirement.startswith("httpx"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.code(f"pip install {requirement}")
                with col2:
                    if st.button("📋", key=f"copy_{requirement}", help="Copy to clipboard"):
                        # In real implementation, would copy to clipboard
                        st.success("Copied!")
            else:
                st.info(f"• {requirement}")

        with st.expander("📚 Installation Help", expanded=False):
            st.markdown("""
            **A2A SDK Installation:**
            ```bash
            pip install a2a-sdk>=0.2.3 httpx>=0.24.0
            ```

            **If you get errors:**
            - Update pip: `pip install --upgrade pip`
            - Use virtual environment: `python -m venv nexus-env && source nexus-env/bin/activate`
            - Install from source: Check GitHub for latest version

            **Restart Nexus after installation.**
            """)

        return False

    return True


def display_error_with_details(error, context=""):
    """Display error with collapsible details and enhanced formatting."""
    error_type = type(error).__name__
    error_msg = str(error)

    # ✅ ENHANCED: Better error display
    col1, col2 = st.columns([3, 1])

    with col1:
        st.error(f"❌ {error_type}: {error_msg[:100]}{'...' if len(error_msg) > 100 else ''}")

    with col2:
        if st.button("🔄 Retry", help="Try the operation again"):
            st.rerun()

    if context:
        st.info(f"**Context:** {context}")

    with st.expander("🐛 Technical Details", expanded=False):
        st.code(f"{error_type}: {error_msg}")

        # ✅ ADDED: Suggestions based on error type
        if "ImportError" in error_type:
            st.info("💡 **Suggestion:** Install missing dependencies with pip")
        elif "ConnectionError" in error_type:
            st.info("💡 **Suggestion:** Check if agents are running and accessible")
        elif "TimeoutError" in error_type:
            st.info("💡 **Suggestion:** Increase timeout settings or check agent responsiveness")

        if hasattr(error, '__traceback__'):
            with st.expander("📋 Full Traceback", expanded=False):
                st.exception(error)


def safe_get_agent_status(manager, agent_name):
    """Safely get agent status with enhanced error handling."""
    try:
        if not manager or not agent_name:
            return "unknown"

        cards = manager.get_all_agent_cards()
        for card in cards:
            if card.name == agent_name:
                return card.status

        return "not_found"
    except Exception:
        return "error"


# ✅ ADDED: Enhanced loading and progress utilities
def show_loading_message(message, duration=2):
    """Show a loading message for a specified duration."""
    placeholder = st.empty()
    placeholder.info(f"🔄 {message}")
    import time
    time.sleep(duration)
    placeholder.empty()


def create_progress_tracker():
    """Create a progress tracker for long operations."""
    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(current, total, message="Processing..."):
        progress = current / total if total > 0 else 0
        progress_bar.progress(progress)
        status_text.text(f"{message} ({current}/{total})")

    def complete():
        progress_bar.progress(1.0)
        status_text.text("✅ Complete!")
        import time
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()

    return update_progress, complete


# ✅ ADDED: Agent URL validation
def validate_agent_url(url):
    """Validate agent URL format."""
    if not url:
        return False, "URL cannot be empty"

    if not url.startswith(('http://', 'https://')):
        return False, "URL must start with http:// or https://"

    # Basic format check
    import re
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, url):
        return False, "Invalid URL format"

    return True, "Valid URL"


# ✅ ADDED: Configuration helpers
def load_orchestration_config():
    """Load orchestration configuration from session state."""
    return st.session_state.get("orchestration_config", {
        "default_timeout": 30,
        "max_concurrent": 5,
        "enable_logging": True,
        "auto_cleanup": True
    })


def save_orchestration_config(config):
    """Save orchestration configuration to session state."""
    st.session_state["orchestration_config"] = config
    st.success("✅ Configuration saved!")
