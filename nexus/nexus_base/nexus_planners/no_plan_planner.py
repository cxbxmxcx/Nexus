# Copyright (c) orginally from Microsoft. (Semantic Kernel)

"""A basic JSON-based planner for Nexus"""

from nexus.nexus_base.planner_manager import NexusPlanner, Plan
from nexus.nexus_base.prompt_template_manager import PromptTemplateManager

PROMPT = """
Generate a chain of thought reasoning strategy 
in order to solve the following problem. 
Just output the reasoning steps and avoid coming
to any conclusions. Also, be sure to avoid any assumptions
and factor in potential unknowns.

[GOAL]
{{$goal}}

[OUTPUT]
"""


def format_action(action):
    name = action["name"]
    description = action["agent_action"]["function"]["description"]
    parameters = action["agent_action"]["function"]["parameters"]["properties"]

    result = f"{name}\ndescription: {description}"
    if parameters:
        result += "\nargs:"
        for param, details in parameters.items():
            param_description = details["description"]
            result += f"\n- {param}: {param_description}"
    return result


class NoPlanPlanner(NexusPlanner):
    def __init__(self):
        super().__init__()

    def create_plan(self, nexus, agent, goal: str, prompt: str = PROMPT) -> Plan:
        """
        Creates a plan for the given goal based off the functions that
        are available.
        """
        selected_actions = nexus.get_actions(agent.actions)
        available_functions_string = "\n\n".join(
            format_action(action) for action in selected_actions
        )

        # Create the context for the planner
        context = {}
        # Add the goal to the context
        context["goal"] = goal
        context["available_functions"] = available_functions_string

        ptm = PromptTemplateManager()
        prompt = ptm.render_prompt(prompt, context)

        plan_text = nexus.execute_prompt(agent, prompt)
        return Plan(prompt=prompt, goal=goal, plan_text=plan_text)

    def execute_plan(self, nexus, agent, plan: Plan) -> str:
        return plan
