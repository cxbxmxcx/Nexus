import json

import gradio as gr

from nexus.gradio_ui.engine_settings_panel import engine_settings_panel
from nexus.nexus_base.nexus import Nexus

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
    planner_options = nexus.get_planner_names() + ["None"]

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
        agent_engine_settings_new = engine_settings_panel()

        def update_engine_settings_new(agent_engine):
            if agent_engine is None:
                return dict(options={}, settings={})
            engine_options, defaults = nexus.get_agent_engine_options_defaults(
                agent_engine
            )
            eos = dict(options=engine_options, settings=defaults)
            return json.dumps(eos, sort_keys=True)

        agent_engine_new.change(
            fn=update_engine_settings_new,
            inputs=[agent_engine_new],
            outputs=[agent_engine_settings_new],
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
            agent_planning_new = gr.Dropdown(
                label="Planner",
                choices=planner_options,
                interactive=True,
                value=planner_options[0],
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

        agent_engine_settings = engine_settings_panel()

        def update_engine_settings(agent_engine):
            if agent_engine is None:
                return dict(options={}, settings={})
            engine_options, defaults = nexus.get_agent_engine_options_defaults(
                agent_engine
            )
            eos = dict(options=engine_options, settings=defaults)
            return json.dumps(eos, sort_keys=True)

        agent_engine.change(
            fn=update_engine_settings,
            inputs=[agent_engine],
            outputs=[agent_engine_settings],
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
            agent_planning = gr.Dropdown(
                label="Planner",
                choices=planner_options,
                interactive=True,
                value=planner_options[0],
            )
            agent_thought_template = gr.Textbox(
                label="Thought Template",
                placeholder="Thought template ID",
            )
        delete_button = gr.Button("🗑️", interactive=True, visible=True)

    def get_agent_details(agent_key):
        agent_options = list_agents()

        if agent_key == CREATE_NEW_AGENT_KEY:
            default_engine = agent_engine_options[0]
            options, settings = nexus.get_agent_engine_options_defaults(default_engine)
            engine_settings = json.dumps(
                dict(options=options, settings=settings), sort_keys=True
            )
            return (
                gr.update(
                    choices=list(agent_options.keys()), value=CREATE_NEW_AGENT_KEY
                ),
                "",
                "",
                "",
                default_engine,
                engine_settings,
                [],
                "{}",
                "{}",
                "{}",
                "{}",
                "None",
                "{}",
                None,
            )
        else:
            if agent_key in agent_options.keys():
                agent_id = agent_options[agent_key]
            else:
                agent_id = agent_key

            agent = nexus.get_agent(agent_id)
            settings = json.loads(agent.engine_settings)
            options, _ = nexus.get_agent_engine_options_defaults(agent.engine)
            engine_settings = json.dumps(
                dict(options=options, settings=settings), sort_keys=True
            )
            actions = json.loads(agent.actions)
            return (
                gr.update(choices=list(agent_options.keys()), value=agent.name),
                agent.name,
                agent.agent_id,
                agent.instructions,
                agent.engine,
                engine_settings,
                actions,
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

    # Cache for storing the last agent data as a string
    agent_cache = {}

    def serialize_agent_data(
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
    ):
        """Serialize agent data to a JSON string."""
        return json.dumps(
            {
                "name": agent_name,
                "agent_id": agent_id,
                "instructions": agent_instructions,
                "engine": agent_engine,
                "engine_settings": agent_engine_settings,
                "actions": agent_actions,
                "memory": agent_memory,
                "knowledge": agent_knowledge,
                "evaluation": agent_evaluation,
                "feedback": agent_feedback,
                "reasoning": agent_reasoning,
                "planning": agent_planning,
                "thought_template": agent_thought_template,
            },
            sort_keys=True,
        )

    def update_agent(
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
    ):
        if agent_id is None or agent_id == "" or len(agent_id) < 10:
            return

        # Serialize the current agent data
        current_agent_data = serialize_agent_data(
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
        )

        # Check if the agent data is different from the cached data
        if agent_cache.get(agent_id) == current_agent_data:
            # No changes detected, skip update
            return

        # Update the cache
        agent_cache[agent_id] = current_agent_data

        # Parse the engine settings
        engine_settings = json.loads(agent_engine_settings)["settings"]
        engine_settings = json.dumps(engine_settings, sort_keys=True)

        actions = [a for a in agent_actions if a in action_choices]
        actions = json.dumps(actions, sort_keys=True)
        # Update the agent
        agent = nexus.update_agent(
            name=agent_name,
            agent_id=agent_id,
            instructions=agent_instructions,
            engine=agent_engine,
            engine_settings=engine_settings,
            actions=actions,
            memory=agent_memory,
            knowledge=agent_knowledge,
            evaluation=agent_evaluation,
            feedback=agent_feedback,
            reasoning=agent_reasoning,
            planning=agent_planning,
            thought_template=agent_thought_template,
        )

    # Bind the debounced update function to the control changes
    for control in controls:
        control.change(
            fn=update_agent,
            inputs=controls,
            outputs=[],
        )

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
        engine_settings = json.dumps(
            json.loads(agent_engine_settings_new)["settings"], sort_keys=True
        )
        actions = [a for a in agent_actions_new if a in action_choices]
        actions = json.dumps(actions, sort_keys=True)
        agent = nexus.create_agent(
            name=agent_name_new,
            instructions=agent_instructions_new,
            engine=agent_engine_new,
            engine_settings=engine_settings,
            actions=actions,
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
