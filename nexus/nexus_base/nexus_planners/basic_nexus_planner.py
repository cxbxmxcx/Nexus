# Copyright (c) orginally from Microsoft. (Semantic Kernel)

"""A basic JSON-based planner for Nexus"""

from nexus.nexus_base.planner_manager import NexusPlanner, Plan
from nexus.nexus_base.prompt_template_manager import PromptTemplateManager

PROMPT = """
You are a planner for Nexus.
Your job is to create a properly formatted JSON plan step by step, to satisfy the goal given.
Create a list of subtasks based off the [GOAL] provided.
Each subtask must be from within the [AVAILABLE FUNCTIONS] list. Do not use any functions that are not in the list.
Base your decisions on which functions to use from the description and the name of the function.
Sometimes, a function may take arguments. Provide them if necessary.
The plan should be as short as possible.
You will also be given a list of corrective, suggestive and epistemic feedback from previous plans to help you make your decision.
For example:

[SPECIAL FUNCTIONS]
for-each- prefix
description: execute a function for each item in a list
args: 
- function: the function to execute
- list: the list of items to iterate over
- index: the arg name for the current item in the list

[AVAILABLE FUNCTIONS]
GetJokeTopics
description: Get a list ([str]) of joke topics

EmailTo
description: email the input text to a recipient
args:
- text: the text to email
- recipient: the recipient's email address. Multiple addresses may be included if separated by ';'.

Summarize
description: summarize input text
args:
- text: the text to summarize

Joke
description: Generate a funny joke
args:
- topic: the topic to generate a joke about

[GOAL]
"Get a list of joke topics and generate a different joke for each topic. Email the jokes to a friend."

[OUTPUT]
    {        
        "subtasks": [
            {"function": "GetJokeTopics"},
            {"function": "for-each", "args": {"list": "output_GetJokeTopics", "index": "topic", "function": {"function": "Joke", "args": {"topic": "topic"}}}},
            {"function": "EmailTo", "args": {"text": "for-each_output_GetJokeTopics", "recipient": "friend"}}
        ]
    }

[AVAILABLE FUNCTIONS]
Brainstorm
description: Brainstorm ideas
args:
- input: the input to brainstorm about

Poe
description: Write in the style of author Edgar Allen Poe
args:
- text: the text to convert to Poe's style

EmailTo
description: Write an email to a recipient
args:
- text: the text of the email
- recipient: the recipient's email address.

Translate
description: translate the text to another language
args:
- text: the text to translate
- language: the language to translate to

[GOAL]
"Tomorrow is Valentine's day. I need to come up with a few date ideas.
She likes Edgar Allen Poe so write using his style.
E-mail these ideas to my significant other. Translate it to French."

[OUTPUT]
    {        
        "subtasks": [
            {"function": "Brainstorm", args: {"input": "Valentine's Day Date Ideas"}},
            {"function": "Poe", "args": {"text": "output_Brainstorm"},
            {"function": "Translate", "args": {"text":"output_Poe", "language": "French"}}
            {"function": "EmailTo", "args": {"text": "output_Translate","recipient": "significant_other"}}            
        ]
    }
    
[SPECIAL FUNCTIONS]
for-each
description: execute a function for each item in a list
args: 
- function: the function to execute
- iterator: the list of items to iterate over
- index: the arg name for the current item in the list  
  
[AVAILABLE FUNCTIONS]
Brainstorm
description: Brainstorm ideas
args:
- input: the input to brainstorm about

Poe
description: Write in the style of author Edgar Allen Poe
args:
- text: the text to convert to Poe's style

EmailTo
description: Write an email to a recipient
args:
- text: the text of the email
- recipient: the recipient's email address.

GetCoworkerEmails
description: returns a list[] of coworker emails

[GOAL]
"Tomorrow I am announcing my retirement.
I need to write a retirement speech in the style of Edgar Allen Poe.
Then I need to send the email to all of my coworkers."

[OUTPUT]    
    {
    "subtasks": [
        { "function": "Brainstorm", "args": { "input": "Retirement Speech Ideas"}},
        { "function": "Poe", "args": { "text": "output_Brainstorm"}},
        { "function": "GetCoworkerEmails"},
        { "function": "for-each", "args": {"list": "output_GetCoworkerEmails","index": "coworker","function": {"function": "EmailTo","args": {"text": "output_Poe","recipient": "coworker"}}}}
    ]
}
    
[SPECIAL FUNCTIONS]
for-each
description: execute a function for each item in a list
args: 
- function: the function to execute
- iterator: the list of items to iterate over
- index: the arg name for the current item in the list  

[AVAILABLE FUNCTIONS]
{{$available_functions}}

[GOAL]
{{$goal}}

Be sure to only use functions from the list of available functions. 
The plan should be as short as possible. 
And only return the plan in JSON format.
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


class BasicNexusPlanner(NexusPlanner):
    """
    Basic JSON-based planner for the Nexus.
    """

    def __init__(self):
        super().__init__()

    def create_plan(self, nexus, agent, goal: str, prompt: str = PROMPT) -> Plan:
        """
        Creates a plan for the given goal based off the functions that
        are available in the kernel.
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
        context = {}
        plan = plan.generated_plan
        for task in plan["subtasks"]:
            if task["function"] == "for-each":
                list_name = task["args"]["list"]
                index_name = task["args"]["index"]
                inner_task = task["args"]["function"]

                list_value = context.get(list_name, [])
                for item in list_value:
                    context[index_name] = item
                    result = nexus.execute_task(agent, inner_task, context)
                    context[f"for-each_{list_name}_{item}"] = result

                # Collect all results of for-each in a single list
                for_each_output = [
                    context[f"for-each_{list_name}_{item}"] for item in list_value
                ]
                context[f"for-each_{list_name}"] = for_each_output
                # now remove the for-each list from the context
                for item in list_value:
                    del context[f"for-each_{list_name}_{item}"]

            else:
                result = nexus.execute_task(agent, task, context)
                context[f"output_{task['function']}"] = result

        return context
