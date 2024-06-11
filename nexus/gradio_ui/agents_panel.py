import time

import gradio as gr

from nexus.nexus_base.nexus import Nexus

# from playground.agents_api import api
# from playground.agents_utils import (
#     get_actions_by_name,
#     get_tools,
#     get_tools_by_name,
# )


def agents_panel(nexus: Nexus):
    available_actions = nexus.get_actions()

    def list_agents():
        agent_choices = nexus.get_agent_names()
        agent_options = {a: a for a in agent_choices}
        agent_options["Create New Agent"] = "new"
        return agent_options

    agent_options = list_agents()

    def update_agent(
        agent_name,
        agent_id,
        agent_instructions,
        agent_model,
        agent_tools,
        agent_actions,
        agent_resformat,
        agent_temperature,
        agent_top_p,
    ):
        if agent_id is not None and len(agent_id) > 5:
            # tools = get_tools_by_name(agent_tools)
            # actions = get_actions_by_name(agent_actions, available_actions)
            # api.update_agent(
            #     agent_name,
            #     agent_id,
            #     agent_instructions,
            #     agent_model,
            #     tools,
            #     actions,
            #     agent_resformat,
            #     agent_temperature,
            #     agent_top_p,
            # )
            pass

    def create_agent(
        agent_name_new,
        agent_instructions_new,
        agent_model_new,
        agent_tools_new,
        agent_actions_new,
        agent_resformat_new,
        agent_temperature_new,
        agent_top_p_new,
    ):
        tools = [
            {"type": "file_search"}
            if tool == "File search"
            else {"type": "code_interpreter"}
            for tool in agent_tools_new
        ]
        actions = [
            action["agent_action"]
            for action in available_actions
            if action["name"] in agent_actions_new
        ]
        format = "auto"  # "type" if agent_resformat_new == "JSON object" else "auto"  TODO: fix this

        # new_agent = api.create_agent(
        #     agent_name_new,
        #     agent_instructions_new,
        #     agent_model_new,
        #     tools,
        #     actions,
        #     format,
        #     agent_temperature_new,
        #     agent_top_p_new,
        # )
        # return new_agent.id
        return "new"

    def get_agent_details(agent_key):
        agent_options = list_agents()
        if agent_key == "Create New Agent":
            return "", "", "", "gpt-4o", [], "", "", 1, 1
        else:
            if agent_key in agent_options.keys():
                agent_id = agent_options[agent_key]
            else:
                agent_id = agent_key

            # agent = api.retrieve_agent(agent_id)
            agent = nexus.get_agent(agent_key)
            actions = []
            if agent.tools is None:
                tools = []
            else:
                # tools, actions = get_tools(agent.tools)
                pass
            format = "type" if agent.response_format == "JSON object" else "auto"

            return (
                agent.name,
                agent.id,
                agent.instructions,
                agent.model,
                tools,
                actions,
                format,
                agent.temperature,
                agent.top_p,
            )

    def agent_selected_change(agent_key):
        if agent_key == "Create New agent":
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
        agent_model_new = gr.Dropdown(
            label="Model",
            choices=["gpt-3", "gpt-3.5", "gpt-4", "gpt-4o"],
            value="gpt-4o",
            interactive=True,
        )
        agent_tools_new = gr.CheckboxGroup(
            label="Tools", choices=["File search", "Code interpreter"], interactive=True
        )
        # agent_files_new = gr.Textbox(
        #     label="Add Files or Functions", placeholder="+ Files, + Functions"
        # )
        with gr.Accordion("Actions", open=False, elem_id="actionsnew"):
            agent_actions_new = gr.CheckboxGroup(
                label="Actions", choices=action_choices, interactive=True
            )
        agent_resformat_new = gr.Radio(
            label="Response Format",
            choices=["JSON object", "Plain text"],
            value="JSON object",
            interactive=True,
        )
        agent_temperature_new = gr.Slider(
            label="Temperature",
            minimum=0,
            maximum=1,
            step=0.01,
            value=1,
            interactive=True,
        )
        agent_top_p_new = gr.Slider(
            label="Top P", minimum=0, maximum=1, step=0.01, value=1, interactive=True
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
        agent_model = gr.Dropdown(
            label="Model",
            choices=["gpt-3", "gpt-3.5", "gpt-4", "gpt-4o"],
            value="gpt-4o",
        )
        agent_tools = gr.CheckboxGroup(
            label="Tools", choices=["File search", "Code interpreter"]
        )
        with gr.Accordion("Actions", open=False, elem_id="actions"):
            agent_actions = gr.CheckboxGroup(
                label="Actions", choices=action_choices, interactive=True
            )
        agent_resformat = gr.Radio(
            label="Response Format",
            choices=["JSON object", "Plain text"],
            value="JSON object",
        )
        agent_temperature = gr.Slider(
            label="Temperature", minimum=0, maximum=1, step=0.01, value=1
        )
        agent_top_p = gr.Slider(label="Top P", minimum=0, maximum=1, step=0.01, value=1)
        delete_button = gr.Button("🗑️")

    agent_selected.change(
        fn=get_agent_details,
        inputs=agent_selected,
        outputs=[
            agent_name,
            agent_id,
            agent_instructions,
            agent_model,
            agent_tools,
            agent_actions,
            agent_resformat,
            agent_temperature,
            agent_top_p,
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
        agent_model,
        agent_tools,
        agent_actions,
        agent_resformat,
        agent_temperature,
        agent_top_p,
    ]

    for control in controls:
        control.change(fn=update_agent, inputs=controls, outputs=[])

    def create_and_select_agent(
        agent_name_new,
        agent_instructions_new,
        agent_model_new,
        agent_tools_new,
        agent_actions_new,
        agent_resformat_new,
        agent_temperature_new,
        agent_top_p_new,
    ):
        new_agent_id = create_agent(
            agent_name_new,
            agent_instructions_new,
            agent_model_new,
            agent_tools_new,
            agent_actions_new,
            agent_resformat_new,
            agent_temperature_new,
            agent_top_p_new,
        )
        time.sleep(2)  # wait for agent to be created
        agent_options = list_agents()
        return (
            gr.update(choices=list(agent_options.keys()), value=new_agent_id),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=True),
        )

    def delete_and_select_agent(agent_id):
        # api.delete_agent(agent_id)
        agent_options = list_agents()
        return (
            gr.update(choices=list(agent_options.keys()), value="Create New agent"),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
        )

    add_button.click(
        fn=create_and_select_agent,
        inputs=[
            agent_name_new,
            agent_instructions_new,
            agent_model_new,
            agent_tools_new,
            agent_actions_new,
            agent_resformat_new,
            agent_temperature_new,
            agent_top_p_new,
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
