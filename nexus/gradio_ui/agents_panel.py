import threading

import gradio as gr

from nexus.nexus_base.nexus import Nexus

# from playground.agents_api import api
# from playground.agents_utils import (
#     get_actions_by_name,
#     get_tools,
#     get_tools_by_name,
# )

# Agents consist of:
# - Name
# - ID
# - Instructions (Persona, purpose, rules, etc.)
# - Engine
# - Engine settings
# - Tools (File search, Code interpreter)
# - Actions (API calls)
# - Memory
# - Knowledge
# - Evaluation
# - Feedback
# - Reasoning
# - Planning
# - Thought process ???
debounce_timer = None


def agents_panel(nexus: Nexus):
    CREATE_NEW_AGENT_KEY = "Create new agent"

    available_actions = nexus.get_actions()

    def list_agents():
        agent_choices = nexus.list_agents()
        agent_options = {a.name: a.agent_id for a in agent_choices}
        agent_options[CREATE_NEW_AGENT_KEY] = "new"
        return agent_options

    agent_options = list_agents()

    def delete_and_select_agent(agent_id):
        # api.delete_agent(agent_id)
        agent_options = list_agents()
        return (
            gr.update(choices=list(agent_options.keys()), value=CREATE_NEW_AGENT_KEY),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
        )

    def agent_selected_change(agent_key):
        if agent_key == CREATE_NEW_AGENT_KEY:
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=False),
            )
        else:
            return (
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=True),
            )

    action_choices = [action["name"] for action in available_actions]
    agent_selected = gr.Dropdown(
        label="Select agent",
        choices=agent_options.keys(),
        interactive=True,
    )

    agent_engine_options = nexus.get_agent_engine_names()

    # Assuming action_choices is defined elsewhere
    # action_choices = [...]

    with gr.Column(visible=False) as new_agent_form:
        agent_name_new = gr.Textbox(
            label="Enter a user-friendly name",
            placeholder="Enter Name",
            interactive=True,
        )
        agent_instructions_new = gr.Textbox(
            label="Instructions",
            placeholder="You are a helpful agent.",
            elem_id="instructions",
            interactive=True,
        )
        agent_engine_new = gr.Dropdown(
            label="Engine",
            choices=agent_engine_options,
            interactive=True,
            value=agent_engine_options[0],
        )
        agent_engine_settings_new = gr.Textbox(
            label="Engine Settings",
            placeholder="{}",
            interactive=True,
            lines=5,
        )
        with gr.Accordion("Actions", open=False, elem_id="actionsnew"):
            agent_actions_new = gr.CheckboxGroup(
                label="Actions", choices=action_choices, interactive=True
            )
        with gr.Accordion("Retrieval", open=False):
            agent_memory_new = gr.Textbox(
                label="Memory",
                placeholder="Memory settings",
                interactive=True,
            )
            agent_knowledge_new = gr.Textbox(
                label="Knowledge",
                placeholder="Knowledge base",
                interactive=True,
            )
        with gr.Accordion("Advanced", open=False):
            agent_evaluation_new = gr.Textbox(
                label="Evaluation",
                placeholder="Evaluation criteria",
                interactive=True,
            )
            agent_feedback_new = gr.Textbox(
                label="Feedback",
                placeholder="Feedback mechanism",
                interactive=True,
            )
            agent_reasoning_new = gr.Textbox(
                label="Reasoning",
                placeholder="Reasoning process",
                interactive=True,
            )
            agent_planning_new = gr.Textbox(
                label="Planning",
                placeholder="Planning details",
                interactive=True,
            )
            agent_thought_template_new = gr.Textbox(
                label="Thought Template",
                placeholder="Thought template ID",
                interactive=True,
            )
        add_button = gr.Button("Add agent", interactive=True, visible=True)

    with gr.Column(visible=True) as existing_agent_form:
        agent_id = gr.Markdown("ID:")
        agent_name = gr.Textbox(
            label="Enter a user-friendly name", placeholder="Enter Name"
        )
        agent_instructions = gr.Textbox(
            label="Instructions",
            placeholder="You are a helpful agent.",
            elem_id="instructions",
        )
        agent_engine = gr.Dropdown(
            label="Engine",
            choices=agent_engine_options,
        )
        agent_engine_settings = gr.Textbox(
            label="Engine Settings",
            placeholder="{}",
            lines=5,
        )
        with gr.Accordion("Actions", open=False, elem_id="actions"):
            agent_actions = gr.CheckboxGroup(
                label="Actions", choices=action_choices, interactive=True
            )
        with gr.Accordion("Retrieval", open=False):
            agent_memory = gr.Textbox(
                label="Memory",
                placeholder="Memory settings",
            )
            agent_knowledge = gr.Textbox(
                label="Knowledge",
                placeholder="Knowledge base",
            )
        with gr.Accordion("Advanced", open=False):
            agent_evaluation = gr.Textbox(
                label="Evaluation",
                placeholder="Evaluation criteria",
            )
            agent_feedback = gr.Textbox(
                label="Feedback",
                placeholder="Feedback mechanism",
            )
            agent_reasoning = gr.Textbox(
                label="Reasoning",
                placeholder="Reasoning process",
            )
            agent_planning = gr.Textbox(
                label="Planning",
                placeholder="Planning details",
            )
            agent_thought_template = gr.Textbox(
                label="Thought Template",
                placeholder="Thought template ID",
            )
        delete_button = gr.Button("🗑️", interactive=True, visible=True)

    def get_agent_details(agent_key):
        agent_options = list_agents()
        if agent_key == CREATE_NEW_AGENT_KEY:
            return (
                gr.update(
                    choices=list(agent_options.keys()), value=CREATE_NEW_AGENT_KEY
                ),
                "",
                "",
                "",
                "gpt-4o",
                "{}",
                [],
                "{}",
                "{}",
                "{}",
                "{}",
                "{}",
                "{}",
                None,
            )
        else:
            if agent_key in agent_options.keys():
                agent_id = agent_options[agent_key]
            else:
                agent_id = agent_key

            agent = nexus.get_agent(agent_id)

            return (
                gr.update(choices=list(agent_options.keys()), value=agent.name),
                agent.name,
                agent.agent_id,
                agent.instructions,
                agent.engine,
                agent.engine_settings,
                agent.actions,
                agent.memory,
                agent.knowledge,
                agent.evaluation,
                agent.feedback,
                agent.reasoning,
                agent.planning,
                agent.thought_template,
            )

    agent_selected.change(
        fn=get_agent_details,
        inputs=agent_selected,
        outputs=[
            agent_selected,
            agent_name,
            agent_id,
            agent_instructions,
            agent_engine,
            agent_engine_settings,
            agent_actions,
            agent_memory,
            agent_knowledge,
            agent_evaluation,
            agent_feedback,
            agent_reasoning,
            agent_planning,
            agent_thought_template,
        ],
    )

    agent_selected.change(
        fn=agent_selected_change,
        inputs=agent_selected,
        outputs=[
            new_agent_form,
            existing_agent_form,
            add_button,
            delete_button,
        ],
    )

    controls = [
        agent_name,
        agent_id,
        agent_instructions,
        agent_engine,
        agent_engine_settings,
        agent_actions,
        agent_memory,
        agent_knowledge,
        agent_evaluation,
        agent_feedback,
        agent_reasoning,
        agent_planning,
        agent_thought_template,
    ]

    def debounce_update_agent(
        agent_name,
        agent_id,
        agent_instructions,
        agent_engine,
        agent_engine_settings,
        agent_actions,
        agent_memory,
        agent_knowledge,
        agent_evaluation,
        agent_feedback,
        agent_reasoning,
        agent_planning,
        agent_thought_template,
        debounce_interval=1,  # debounce interval in seconds
    ):
        global debounce_timer

        def execute_update():
            if agent_id is None or agent_id == "" or agent_id == "ID:":
                return

            nexus.update_agent(
                name=agent_name,
                agent_id=agent_id,
                instructions=agent_instructions,
                engine=agent_engine,
                engine_settings=agent_engine_settings,
                actions=agent_actions,
                memory=agent_memory,
                knowledge=agent_knowledge,
                evaluation=agent_evaluation,
                feedback=agent_feedback,
                reasoning=agent_reasoning,
                planning=agent_planning,
                thought_template=agent_thought_template,
            )

        # Cancel the previous timer if it exists
        if debounce_timer is not None:
            debounce_timer.cancel()

        # Set a new timer
        debounce_timer = threading.Timer(debounce_interval, execute_update)
        debounce_timer.start()

    # Bind the debounced update function to the control changes
    for control in controls:
        control.change(
            fn=lambda agent_name,
            agent_id,
            agent_instructions,
            agent_engine,
            agent_engine_settings,
            agent_actions,
            agent_memory,
            agent_knowledge,
            agent_evaluation,
            agent_feedback,
            agent_reasoning,
            agent_planning,
            agent_thought_template: debounce_update_agent(
                agent_name,
                agent_id,
                agent_instructions,
                agent_engine,
                agent_engine_settings,
                agent_actions,
                agent_memory,
                agent_knowledge,
                agent_evaluation,
                agent_feedback,
                agent_reasoning,
                agent_planning,
                agent_thought_template,
            ),
            inputs=controls,
            outputs=[],
        )

    # def update_agent(
    #     agent_name,
    #     agent_id,
    #     agent_instructions,
    #     agent_engine,
    #     agent_engine_settings,
    #     agent_actions,
    #     agent_memory,
    #     agent_knowledge,
    #     agent_evaluation,
    #     agent_feedback,
    #     agent_reasoning,
    #     agent_planning,
    #     agent_thought_template,
    # ):
    #     if agent_id is None or agent_id == "" or agent_id == "ID:":
    #         return

    #     nexus.update_agent(
    #         name=agent_name,
    #         agent_id=agent_id,
    #         instructions=agent_instructions,
    #         engine=agent_engine,
    #         engine_settings=agent_engine_settings,
    #         actions=agent_actions,
    #         memory=agent_memory,
    #         knowledge=agent_knowledge,
    #         evaluation=agent_evaluation,
    #         feedback=agent_feedback,
    #         reasoning=agent_reasoning,
    #         planning=agent_planning,
    #         thought_template=agent_thought_template,
    #     )

    # for control in controls:
    #     control.change(fn=update_agent, inputs=controls, outputs=[])

    def create_and_select_agent(
        agent_name_new,
        agent_instructions_new,
        agent_engine_new,
        agent_engine_settings_new,
        agent_actions_new,
        agent_memory_new,
        agent_knowledge_new,
        agent_evaluation_new,
        agent_feedback_new,
        agent_reasoning_new,
        agent_planning_new,
        agent_thought_template_new,
    ):
        agent = nexus.create_agent(
            name=agent_name_new,
            instructions=agent_instructions_new,
            engine=agent_engine_new,
            engine_settings=agent_engine_settings_new,
            actions=agent_actions_new,
            memory=agent_memory_new,
            knowledge=agent_knowledge_new,
            evaluation=agent_evaluation_new,
            feedback=agent_feedback_new,
            reasoning=agent_reasoning_new,
            planning=agent_planning_new,
            thought_template=agent_thought_template_new,
        )
        agent_options = list_agents()
        return (
            gr.update(choices=list(agent_options.keys()), value=agent.name),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=True),
        )

    add_button.click(
        fn=create_and_select_agent,
        inputs=[
            agent_name_new,
            agent_instructions_new,
            agent_engine_new,
            agent_engine_settings_new,
            agent_actions_new,
            agent_memory_new,
            agent_knowledge_new,
            agent_evaluation_new,
            agent_feedback_new,
            agent_reasoning_new,
            agent_planning_new,
            agent_thought_template_new,
        ],
        outputs=[
            agent_selected,
            new_agent_form,
            existing_agent_form,
            add_button,
            delete_button,
        ],
    )

    delete_button.click(
        fn=delete_and_select_agent,
        inputs=[agent_id],
        outputs=[
            agent_selected,
            new_agent_form,
            existing_agent_form,
            add_button,
            delete_button,
        ],
    )

    return agent_id
