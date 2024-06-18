from datetime import datetime

from nexus.nexus_base.action_manager import agent_action


@agent_action
def get_current_date_and_time():
    """Returns the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
