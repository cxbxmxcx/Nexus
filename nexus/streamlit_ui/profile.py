import streamlit as st

from nexus.streamlit_ui.cache import get_nexus

# def display_profile(profile):
#     # Use columns to organize the layout
#     col1, col2 = st.columns(2)

#     with col1:
#         profile.name = st.text_input("Name", value=profile.name)
#         profile.avatar = st.text_input("Avatar", value=profile.avatar)
#         profile.persona = st.text_area("Persona", value=profile.persona)

#     with col2:
#         # Safely handle actions, knowledge, memory which could be None
#         actions = ", ".join(profile.actions) if profile.actions else ""
#         profile.actions = [
#             action.strip()
#             for action in st.text_input("Actions (comma-separated)", actions).split(",")
#             if action
#         ]

#         knowledge = ", ".join(profile.knowledge) if profile.knowledge else ""
#         profile.knowledge = [
#             item.strip()
#             for item in st.text_input("Knowledge (comma-separated)", knowledge).split(
#                 ","
#             )
#             if item
#         ]

#         memory = ", ".join(profile.memory) if profile.memory else ""
#         profile.memory = [
#             item.strip()
#             for item in st.text_input("Memory (comma-separated)", memory).split(",")
#             if item
#         ]

#     # Placeholders for complex structures. Implement appropriate JSON/string editors if necessary.
#     profile.evaluators = st.text_area("Evaluators (JSON structure)", "Not implemented")
#     profile.reasoners = st.text_area("Reasoners (JSON structure)", "Not implemented")
#     profile.planners = st.text_area("Planners (JSON structure)", "Not implemented")
#     profile.feedback = st.text_area("Feedback (JSON structure)", "Not implemented")


def profile_page(username, win_height):
    chat = get_nexus()
    user = chat.get_participant(username)
    if user is None:
        st.error("Invalid user")
        st.stop()

    profiles = chat.get_profile_names()

    # Data storage using a dictionary
    profiles = {}

    def save_profile(name, profile_data):
        profiles[name] = profile_data

    def delete_profile(name):
        del profiles[name]

    def get_profile_choices():
        return ["Create New Profile"] + list(profiles.keys())

    prompt_templates = ["Template 1", "Template 2", "Template 3"]

    st.title("Agent Profile Management")

    # Dropdown to select or create a new profile
    profile_choice = st.selectbox(
        "Select a profile to edit or create a new one", get_profile_choices()
    )

    # Initialize variables
    name = ""
    description = ""
    persona = ""
    actions = []
    knowledge_store = []
    memory_store = []
    reasoning = ""
    evaluation = ""
    planning = ""
    feedback = ""
    execution_template = ""

    delete_button = None

    if profile_choice != "Create New Profile":
        profile_data = profiles[profile_choice]
        name = profile_data["name"]
        description = profile_data["description"]
        persona = profile_data["persona"]
        actions = profile_data["actions"]
        knowledge_store = profile_data["knowledge_store"]
        memory_store = profile_data["memory_store"]
        reasoning = profile_data["reasoning"]
        evaluation = profile_data["evaluation"]
        planning = profile_data["planning"]
        feedback = profile_data["feedback"]
        execution_template = profile_data["execution_template"]

    with st.sidebar.form("profile_form"):
        st.text_input(
            "Name",
            value=name if profile_choice != "Create New Profile" else "",
            key="name",
        )
        st.text_area("Description", value=description, key="description")
        st.text_area("Persona", value=persona, key="persona")
        st.multiselect(
            "Actions",
            ["Action 1", "Action 2", "Action 3"],
            default=actions,
            key="actions",
        )
        st.multiselect(
            "Knowledge Store",
            ["Store 1", "Store 2"],
            default=knowledge_store,
            key="knowledge_store",
        )
        st.multiselect(
            "Memory Store",
            ["Memory 1", "Memory 2"],
            default=memory_store,
            key="memory_store",
        )
        st.selectbox(
            "Reasoning",
            prompt_templates,
            index=prompt_templates.index(reasoning) if reasoning else 0,
            key="reasoning",
        )
        st.selectbox(
            "Evaluation",
            prompt_templates,
            index=prompt_templates.index(evaluation) if evaluation else 0,
            key="evaluation",
        )
        st.selectbox(
            "Planning",
            prompt_templates,
            index=prompt_templates.index(planning) if planning else 0,
            key="planning",
        )
        st.selectbox(
            "Feedback",
            prompt_templates,
            index=prompt_templates.index(feedback) if feedback else 0,
            key="feedback",
        )
        st.selectbox(
            "Execution Template",
            prompt_templates,
            index=prompt_templates.index(execution_template)
            if execution_template
            else 0,
            key="execution_template",
        )

        if profile_choice == "Create New Profile":
            submit_button = st.form_submit_button("Create Profile")
        else:
            submit_button = st.form_submit_button("Update Profile")
            delete_button = st.form_submit_button("Delete Profile")

    if submit_button:
        profile_data = {
            "name": st.session_state.name,
            "description": st.session_state.description,
            "persona": st.session_state.persona,
            "actions": st.session_state.actions,
            "knowledge_store": st.session_state.knowledge_store,
            "memory_store": st.session_state.memory_store,
            "reasoning": st.session_state.reasoning,
            "evaluation": st.session_state.evaluation,
            "planning": st.session_state.planning,
            "feedback": st.session_state.feedback,
            "execution_template": st.session_state.execution_template,
        }
        save_profile(name, profile_data)
        st.success(
            "Profile saved!"
            if profile_choice == "Create New Profile"
            else "Profile updated!"
        )
        st.rerun()

    if delete_button:
        delete_profile(profile_choice)
        st.success("Profile deleted!")
        # Reset the select box
        st.rerun()
