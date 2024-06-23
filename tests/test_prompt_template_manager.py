from nexus.nexus_base.prompt_template_manager import PromptTemplateManager


def test_render_prompt():
    # Test rendering the template with the context
    template = """
    ```json
    {
        "available_functions": "Function 1, Function 2",
        "available_feedback": "Feedback 1, Feedback 2",
        "goal": "Complete the task"
    }
    ```    
    [AVAILABLE FUNCTIONS]
    {{$available_functions}}

    [AVAILABLE FEEDBACK]
    {{$available_feedback}}

    [GOAL]
    {{$goal}}
    """
    ptm = PromptTemplateManager()
    rendered_template = ptm.render_prompt(
        template,
        context={
            "available_functions": "Function 1, Function 2",
            "available_feedback": "Feedback 1, Feedback 2",
            "goal": "Complete the task",
        },
    )
    assert (
        rendered_template
        == """
    ```json
    {
        "available_functions": "Function 1, Function 2",
        "available_feedback": "Feedback 1, Feedback 2",
        "goal": "Complete the task"
    }
    ```
    [AVAILABLE FUNCTIONS]
    Function 1, Function 2

    [AVAILABLE FEEDBACK]
    Feedback 1, Feedback 2

    [GOAL]
    Complete the task
    """
    )
