import pytest

from nexus.nexus_base.nexus import Nexus
from nexus.nexus_base.nexus_models import ThoughtTemplate
from nexus.nexus_base.thought_template_manager import ThoughtTemplateManager


@pytest.fixture
def nexus():
    # Create an instance of Nexus for testing
    return Nexus()


@pytest.fixture
def thought_template_manager(nexus):
    # Create an instance of PromptTemplateManager for testing
    return ThoughtTemplateManager(nexus)


@pytest.fixture
def agent(nexus):
    # Create an instance of Agent for testing
    agent_name = "GroqAgent"
    profile_name = "Adam"
    agent = nexus.get_agent(agent_name)
    profile = nexus.get_profile(profile_name)
    agent.profile = profile
    return nexus.get_agent(agent_name)


def test_execute_simple_input_template(thought_template_manager, agent):
    # Define the test inputs
    content = """        
        inputs:
            type: prompt
            name:
                type: string
            template: |
                I am {{name}}, what is your name?
    """
    inputs = {"name": "John"}

    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = thought_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    # Perform assertions to verify the expected outputs
    assert iprompt == "I am John, what is your name?\n"
    assert oprompt is None
    assert iresult is not None
    assert oresult is None


def test_bad_yaml_input_template(thought_template_manager, agent):
    # Define the test inputs
    content = """
    inputs: -
        type: prompt
        inputs:
            name:
                type: string
            template: |
                I am {{ name }}, what is your name?
    """
    inputs = {"name": "John"}

    # Call the execute_template function
    exception = True
    try:
        iprompt, iresult, oprompt, oresult = thought_template_manager.execute_template(
            agent, content, inputs, outputs={}, partial_execution=False
        )
        exception = False
    except Exception as e:
        assert str(e).startswith("Error loading YAML content:")

    assert exception


def test_bad_yaml_output_template(thought_template_manager, agent):
    # Define the test inputs
    content = """
    outputs: -
        type: string
        template: |
            Hello, {{ output }}!
    """
    inputs = {"name": "John"}

    # Call the execute_template function
    exception = True
    try:
        iprompt, iresult, oprompt, oresult = thought_template_manager.execute_template(
            agent, content, inputs, outputs={}, partial_execution=False
        )
        exception = False
    except Exception as e:
        assert str(e).startswith("Error loading YAML content:")

    assert exception


def test_bad_template_content(thought_template_manager, agent):
    # Define the test inputs
    content = """
    inputs:
        type: prompt
        name:
            type: string
        template: |
            I am {{name }}, what is your name?    
    """
    inputs = {"name": "John"}

    # Call the execute_template function
    exception = True
    try:
        iprompt, iresult, oprompt, oresult = thought_template_manager.execute_template(
            agent, content, inputs, outputs={}, partial_execution=False
        )
        exception = False
    except Exception as e:
        assert str(e).startswith("Unexpected token")

    assert exception


def test_get_thought_template_with_monkeypatch(nexus, monkeypatch):
    # Function to replace get_thought_template
    def mock_get_thought_template():
        return "Your mock template"

    # Use monkeypatch to replace the real function with your mock
    monkeypatch.setattr(nexus, "get_thought_template", mock_get_thought_template)

    # Now calling nexus.get_prompt_template() will use the mock function
    result = nexus.get_thought_template()
    assert result == "Your mock template"


def test_execute_partial_input_template(thought_template_manager, agent, monkeypatch):
    # Define the test inputs
    def mock_get_thought_template(self):
        content = """        
        inputs:
            type: function
            name:
                type: string
            template: |
                {{name}} - {{name}}
        """
        return ThoughtTemplate(
            content=content, inputs={}, outputs={}, name="partial_test"
        )

    # Use monkeypatch to replace the real function with your mock
    monkeypatch.setattr(
        thought_template_manager, "get_thought_template", mock_get_thought_template
    )
    content = """        
        inputs:
            type: prompt
            name:
                type: string
            template: |
                I am {{>partial_test name}}, what is your name?"""
    inputs = {"name": "John"}

    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = thought_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    # Perform assertions to verify the expected outputs
    assert iprompt == "I am John - John\n, what is your name?"
    assert oprompt is None
    assert iresult is not None
    assert oresult is None


def test_execute_template(thought_template_manager, agent):
    # Define the test inputs
    content = """        
        inputs:
            type: prompt
            name:
                type: string
            template: |
                I am {{name}}, what is your name?
        outputs:
            type: function
            output:
                type: string                
            template: "Hello, {{output}}!"
    """
    inputs = {"name": "John"}

    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = thought_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt == "I am John, what is your name?\n"
    assert iresult is not None
    assert oprompt.startswith("Hello,")
    assert oresult is not None


def test_helper_template(thought_template_manager, agent):
    content = """        
        inputs:
            input:
                type: string
            template: |
                {{#upper input}}
        helpers:
            upper: |
                def upper(arg):
                    return arg.upper()          
    """
    inputs = {"input": "hello"}
    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = thought_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt == "HELLO\n"
    assert iresult == "HELLO\n"


def test_template_multiple_args(thought_template_manager, agent):
    content = """        
        inputs:
            type: function
            input:
                type: string
            name:
                type: string
            template: |
                {{input}}   {{name}}
    """
    inputs = {"input": "hello", "name": "world"}
    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = thought_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt.startswith("hello   world")
    assert iresult.startswith("hello   world")


def test_helper_template_multiple_args(thought_template_manager, agent):
    content = """        
        inputs:
            input:
                type: string
            name:
                type: string
            template: |
                {{#add input name}}
        helpers:
            add: |
                def add(arg1, arg2):
                    return arg1.upper() + arg2         
    """
    inputs = {"input": "hello", "name": "world"}
    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = thought_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt == "HELLOworld\n"
    assert iresult == "HELLOworld\n"

    # Add more test cases as needed


def test_input_output_thoughts(thought_template_manager, agent):
    content = """        
        inputs:
            type: prompt
            input:
                type: string
            name:
                type: string
            template: |
                {{input}}   {{name}}
        outputs:
            type: prompt
            output:
                type: string
            name:
                type: string
            template: |
                {{output}}   {{name}}
    """
    inputs = {"input": "hello", "name": "world"}
    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = thought_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt == "hello   world\n"
    assert iresult is not None
    assert oprompt.endswith("world\n")
    assert oresult is not None


def test_reasoning_evaluation_partials(thought_template_manager, agent, monkeypatch):
    # Define the test inputs
    def mock_get_thought_template(arg):
        if arg == "reasoning":
            content = """        
            inputs:
                type: prompt
                input:
                    type: string
                template: |
                    Generate a chain of thought reasoning strategy 
                    in order to solve the following problem. 
                    Just output the reasoning steps and avoid coming
                    to any conclusions. Also, be sure to avoid any assumptions
                    and factor in potential unknowns.
                    {{input}}
            """
        elif arg == "evaluation":
            content = """        
            inputs:
                type: prompt
                input:
                    type: string
                output:
                    type: string
                template: |
                    Provided the following problem:
                    {{input}}
                    and the solution {{output}}
                    Evaluate how successful the problem 
                    was solved and return a score 0.0 to 1.0.
                    """

        return ThoughtTemplate(
            content=content, inputs={}, outputs={}, name="partial_test"
        )

    # Use monkeypatch to replace the real function with your mock
    monkeypatch.setattr(
        thought_template_manager, "get_thought_template", mock_get_thought_template
    )
    content = """        
        inputs:
            type: prompt
            input:
                type: string
            template: |
                problem: {{input}}
                reasoning: {{>reasoning input}}

        outputs:
            type: prompt
            input:
                string
            output:
                type: string
            template: |
                evaluation: {{>evaluation input output}}
    """
    inputs = {"input": "who would win a peck off, a rooster or a tiger?"}

    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = thought_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    # Perform assertions to verify the expected outputs
    assert iprompt.startswith(
        "problem: who would win a peck off, a rooster or a tiger?"
    )
    assert oprompt is not None
    assert iresult is not None
    assert oresult is not None


def test_helper_agent_functions(thought_template_manager, agent):
    content = """        
        inputs:
            type: function            
            template: |                
                Agent type: {{#agent_name}} 
                Memory: {{#memory_store}}
        helpers:
            agent_name: |
                def agent_name():
                    return agent.name
            memory_store: |
                def memory_store():
                    return agent.memory_store        
    """
    inputs = {}
    agent.memory_store = "my_memory"
    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = thought_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt == f"Agent type: {agent.name} \nMemory: {agent.memory_store}\n"
    assert iresult == f"Agent type: {agent.name} \nMemory: {agent.memory_store}\n"
    assert oprompt is None
    assert oresult is None


def test_helper_nexus_functions(thought_template_manager, agent):
    content = """        
        inputs:
            type: function 
            agent:
                type: string         
            template: |                
                Agent: {{#get_agent agent}} 
                Users: {{#get_users}}
        helpers:
            get_agent: |
                def get_agent(agent_name):
                    return nexus.get_agent(agent_name).name
            get_users: |
                def get_users():
                    users = nexus.get_all_participants()
                    return str(users)
    """
    inputs = {"agent": "GroqAgent"}

    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = thought_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt is not None
    assert iresult is not None
    assert oprompt is None
    assert oresult is None


def test_basic_planning_thought(thought_template_manager, agent):
    content = """
inputs:
    type: prompt
    input:
        type: string
    template: |
        You are a planner for the Nexus.
        Your job is to create a properly formatted JSON plan step by step, to satisfy the goal given.
        Create a list of subtasks based off the [GOAL] provided.
        Each subtask must be from within the [AVAILABLE FUNCTIONS] list. Do not use any functions that are not in the list.
        Base your decisions on which functions to use from the description and the name of the function.
        Sometimes, a function may take arguments. Provide them if necessary.
        The plan should be as short as possible.
        You will also be given a list of corrective, suggestive and epistemic feedback from previous plans to help you make your decision.
        For example:

        [AVAILABLE FUNCTIONS]
        EmailConnector.LookupContactEmail
        description: looks up the a contact and retrieves their email address
        args:
        - name: the name to look up

        WriterSkill.EmailTo
        description: email the input text to a recipient
        args:
        - input: the text to email
        - recipient: the recipient's email address. Multiple addresses may be included if separated by ';'.

        WriterSkill.Translate
        description: translate the input to another language
        args:
        - input: the text to translate
        - language: the language to translate to

        WriterSkill.Summarize
        description: summarize input text
        args:
        - input: the text to summarize

        FunSkill.Joke
        description: Generate a funny joke
        args:
        - input: the input to generate a joke about

        [GOAL]
        "Tell a joke about cars. Translate it to Spanish"

        [OUTPUT]
            {
                "input": "cars",
                "subtasks": [
                    {"function": "FunSkill.Joke"},
                    {"function": "WriterSkill.Translate", "args": {"language": "Spanish"}}
                ]
            }

        [AVAILABLE FUNCTIONS]
        WriterSkill.Brainstorm
        description: Brainstorm ideas
        args:
        - input: the input to brainstorm about

        EdgarAllenPoeSkill.Poe
        description: Write in the style of author Edgar Allen Poe
        args:
        - input: the input to write about

        WriterSkill.EmailTo
        description: Write an email to a recipient
        args:
        - input: the input to write about
        - recipient: the recipient's email address.

        WriterSkill.Translate
        description: translate the input to another language
        args:
        - input: the text to translate
        - language: the language to translate to

        [GOAL]
        "Tomorrow is Valentine's day. I need to come up with a few date ideas.
        She likes Edgar Allen Poe so write using his style.
        E-mail these ideas to my significant other. Translate it to French."

        [OUTPUT]
            {
                "input": "Valentine's Day Date Ideas",
                "subtasks": [
                    {"function": "WriterSkill.Brainstorm"},
                    {"function": "EdgarAllenPoeSkill.Poe"},
                    {"function": "WriterSkill.EmailTo", "args": {"recipient": "significant_other"}},
                    {"function": "WriterSkill.Translate", "args": {"language": "French"}}
                ]
            }

        [AVAILABLE FUNCTIONS]
        {{#available_functions}}

        [GOAL]
        {{input}}

        [OUTPUT]
outputs:                
    type: prompt                
    output:
        type: string
    template: |
        {{#execute output}}
    
helpers:
    # Defines a method to augment the knowledge of the input
    available_functions: |
        def available_functions():
            return ""
            
            
    # Defines a method to execute the plan
    execute: |
        def execute(output):
            return ""
    """
    inputs = {"input": "hello"}
    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = thought_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt is not None
    assert iresult is not None
    assert oprompt is not None
    assert oresult is not None
