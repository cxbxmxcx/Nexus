import inspect
import json
import os

import streamlit as st
from code_editor import code_editor

from nexus.streamlit_ui.agent_panel import agent_panel
from nexus.streamlit_ui.cache import get_nexus
from nexus.streamlit_ui.options import create_editor_options_ui


def prompts_page(username, win_height):
    chat = get_nexus()
    user = chat.get_participant(username)
    if user is None:
        st.error("Invalid user")
        st.stop()

    with st.sidebar.container(height=600):
        agent = agent_panel(chat)

    # UI for the app
    st.header("Prompt Function Template Manager")
    prompt_names = chat.get_prompt_template_names()
    template_names = ["Create New Template"] + sorted(prompt_names)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    editor_commands_path = os.path.join(current_dir, "editor_commands.json")

    with open(editor_commands_path) as json_info_file:
        btns = json.load(json_info_file)

    result = None

    left_column, right_column = st.columns([4, 4])

    with left_column:
        selected_template_name = st.selectbox("Select a template", template_names)
        if selected_template_name == "Create New Template":
            new_name = st.text_input("Template Name").strip()
            height, language, theme, shortcuts, focus = create_editor_options_ui()
            response_dict = code_editor(
                "",
                height=height,
                lang=language,
                theme=theme,
                shortcuts=shortcuts,
                focus=focus,
                buttons=btns,
            )
            new_content = response_dict["text"]

            if new_name and new_content:
                if response_dict["type"] == "saved":
                    try:
                        # Save the new template
                        chat.add_prompt_template(
                            new_name,
                            new_content,
                        )
                        st.success(f"Prompt Template '{new_name}' added!")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                        st.stop()

        elif selected_template_name:
            # Load and display the selected template for editing
            selected_template = chat.get_prompt_template(selected_template_name)
            edited_name = st.text_input("Template Name", value=selected_template_name)
            height, language, theme, shortcuts, focus = create_editor_options_ui()
            response_dict = code_editor(
                selected_template.content,
                height=height,
                lang=language,
                theme=theme,
                shortcuts=shortcuts,
                focus=focus,
                buttons=btns,
            )
            edited_content = response_dict["text"]

            col1, col2 = st.columns([1, 1])
            with col1:
                if edited_content and response_dict["type"] == "saved":
                    # Update the template with new values
                    chat.update_prompt_template(
                        edited_name,
                        edited_content,
                    )
                    if edited_name != selected_template_name:
                        # If the name was edited, delete the old entry after saving the new one
                        chat.delete_prompt_template(selected_template_name)
                    st.success(f"Template '{edited_name}' updated!")
            with col2:
                if st.button("Delete Template") or response_dict["type"] == "delete":
                    chat.delete_prompt_template(selected_template_name)
                    st.success(f"Template '{selected_template_name}' deleted!")
                    st.rerun()

        with st.expander("Nexus and Agent Methods", expanded=False):
            options = {"Nexus": chat.__class__, "Agent": agent.__class__}
            # Streamlit UI to select between Nexus and Agent
            selected_option = st.selectbox("Select an object:", options.keys())
            # Get the class based on the selected option
            selected_class = options[selected_option]
            # Extract methods from the selected class
            methods = [
                method_name
                for method_name, _ in inspect.getmembers(
                    selected_class, predicate=inspect.isfunction
                )
            ]
            # UI to select a method from the selected class
            selected_method_name = st.selectbox(
                f"Select a method of {selected_option}:", methods
            )
            if selected_method_name:
                # Get the method object from the class
                selected_method = getattr(selected_class, selected_method_name)
                # Display the method's signature and documentation
                st.write(f"##### Signature for `{selected_method_name}`:")
                st.code(inspect.signature(selected_method))
                st.write(f"##### Documentation for `{selected_method_name}`:")
                st.code(selected_method.__doc__)

    with right_column:
        # Use the current content and inputs from the left column for testing
        current_content = (
            new_content
            if selected_template_name == "Create New Template"
            else edited_content
        )

        if current_content:
            current_inputs, current_outputs = chat.get_prompt_template_inputs_outputs(
                current_content
            )
            inputs = {}
            for field in current_inputs.keys():
                field = field.strip()  # Clean up whitespace
                if field:  # Ensure the field is not empty
                    inputs[field] = st.text_input(f"Value for {field}", key=field)

            if st.button("Run Test", key="test"):
                with st.spinner(text="Executing prompt/function by Agent..."):
                    iprompt, iresult, oprompt, oresult = chat.execute_template(
                        agent, current_content, inputs, current_outputs
                    )

                if iresult:
                    with st.container():
                        st.subheader("Input Prompt")
                        st.write(iprompt)
                        st.subheader("Response")
                        st.write(iresult)
                if oresult:
                    with st.container():
                        st.subheader("Output Response")
                        st.write(oprompt)
                        st.subheader("Output Prompt Response")
                        st.write(oresult)
