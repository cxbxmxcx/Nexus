# Define the functions mentioned in the execution plans


def GetJokeTopics():
    # Example function that returns a list of joke topics
    return ["Animals", "Technology", "School"]


def Joke(topic):
    # Example function that returns a joke based on the topic
    jokes = {
        "Animals": "Why did the chicken join a band? Because it had the drumsticks!",
        "Technology": "Why do programmers prefer dark mode? Because light attracts bugs!",
        "School": "Why was the math book sad? Because it had too many problems!",
    }
    return jokes.get(topic, "No jokes available for this topic.")


def EmailTo(text, recipient):
    # Example function to send an email (simplified for demonstration)
    # Replace these with actual email sending logic
    print(f"Sending email to {recipient} with text: {text}")
    return f"Email sent to {recipient}"


def Brainstorm(input):
    # Example function that returns brainstormed ideas
    return ["Idea 1", "Idea 2", "Idea 3"]


def Poe(text):
    # Example function that modifies text (e.g., adds a poetic touch)
    return f"Poetic version of: {text}"


def GetCoworkerEmails():
    # Example function that returns a list of coworker emails
    return ["coworker1@example.com", "coworker2@example.com"]


# Helper function to execute tasks
def execute_task(task, context):
    function_name = task.get("function")
    args = task.get("args", {}).copy()

    # Replace argument values with context outputs if needed
    for key, value in args.items():
        if isinstance(value, str) and value.startswith("output_"):
            args[key] = context.get(value, value)
        else:
            args[key] = context.get(value, value)

    # Get the function from globals and execute it with arguments
    function = globals().get(function_name)
    if function:
        result = function(**args)
        return result


def execute_plan(plan):
    context = {}
    for task in plan["subtasks"]:
        if task["function"] == "for-each":
            list_name = task["args"]["list"]
            index_name = task["args"]["index"]
            inner_task = task["args"]["function"]

            list_value = context.get(list_name, [])
            for item in list_value:
                context[index_name] = item
                result = execute_task(inner_task, context)
                context[f"for-each_{list_name}_{item}"] = result

            # Collect all results of for-each in a single list
            for_each_output = [
                context[f"for-each_{list_name}_{item}"] for item in list_value
            ]
            context[f"for-each_{list_name}"] = for_each_output
        else:
            result = execute_task(task, context)
            context[f"output_{task['function']}"] = result

    return context


# Example 1
execution_plan_1 = {
    "subtasks": [
        {"function": "Brainstorm", "args": {"input": "Retirement Speech Ideas"}},
        {"function": "Poe", "args": {"text": "output_Brainstorm"}},
        {"function": "GetCoworkerEmails"},
        {
            "function": "for-each",
            "args": {
                "list": "output_GetCoworkerEmails",
                "index": "coworker",
                "function": {
                    "function": "EmailTo",
                    "args": {"text": "output_Poe", "recipient": "coworker"},
                },
            },
        },
    ]
}

# Example 2
execution_plan_2 = {
    "subtasks": [
        {"function": "GetJokeTopics"},
        {
            "function": "for-each",
            "args": {
                "list": "output_GetJokeTopics",
                "index": "topic",
                "function": {"function": "Joke", "args": {"topic": "topic"}},
            },
        },
        {
            "function": "EmailTo",
            "args": {"text": "for-each_output_GetJokeTopics", "recipient": "friend"},
        },
    ]
}


def test_this_code():
    # Execute the plans
    context_1 = execute_plan(execution_plan_1)
    context_2 = execute_plan(execution_plan_2)

    print(context_1)
    print(context_2)
