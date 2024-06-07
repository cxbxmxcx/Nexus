from nexus.nexus_base.action_manager import agent_action


@agent_action
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    return f"The current weather in {location} is 0 {unit}."


@agent_action
def recommend(topic):
    """
    System:
        Provide a recommendation for a given {{topic}}.
        Use your best judegment to provide a recommendation.
    User:
        please use your best judgement
        to provide a recommendation for {{topic}}.
    """
    pass
