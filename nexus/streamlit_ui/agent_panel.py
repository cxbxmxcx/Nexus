import streamlit as st

from nexus.streamlit_ui.options import create_options_ui


def agent_panel(nexus):
    st.title("Agent Settings")
    agent_engines = nexus.get_agent_engine_names()
    selected_engine = st.selectbox(
        "Choose an agent engine:",
        agent_engines,
        key="agents",
        # label_visibility="collapsed",
        help="Choose an agent to chat with.",
    )
    agent_engine = nexus.get_agent(selected_engine)
    with st.expander("Agent Options:", expanded=False):
        options = agent_engine.get_attribute_options()
        if options:
            selected_options = create_options_ui(options)
            for key, value in selected_options.items():
                setattr(agent_engine, key, value)

    # profiles = nexus.get_profile_names()

    def format_agent_profile(agent_name):
        profile = nexus.get_profile(agent_name)
        return f"{profile.avatar} : {profile.name}"

    # selected_profile = st.selectbox(
    #     "Choose an agent profile:",
    #     profiles,
    #     key="profiles",
    #     # label_visibility="collapsed",
    #     help="Choose a profile for your agent.",
    #     format_func=format_agent_profile,
    # )

    # chat_agent.actions = []
    # if chat_agent.supports_actions:
    #     action_names = chat.get_action_names()
    #     selected_action_names = st.multiselect(
    #         "Select actions:",
    #         action_names,
    #         key="actions",
    #         # label_visibility="collapsed",
    #         help="Choose the actions the agent can use.",
    #     )
    #     selected_actions = chat.get_actions(selected_action_names)
    #     chat_agent.actions = selected_actions

    # chat_agent.knowledge_store = "None"
    # if chat_agent.supports_knowledge:
    #     knowledge_stores = chat.get_knowledge_store_names()
    #     selected_knowledge_store = st.selectbox(
    #         "Select a knowledge store:",
    #         ["None"] + knowledge_stores,
    #         key="knowledge_store",
    #         # label_visibility="collapsed",
    #         help="Choose the knowledge store to use.",
    #     )
    #     chat_agent.knowledge_store = selected_knowledge_store

    # chat_agent.memory_store = "None"
    # if chat_agent.supports_memory:
    #     memory_stores = chat.get_memory_store_names()
    #     selected_memory_store = st.selectbox(
    #         "Select a memory store:",
    #         ["None"] + memory_stores,
    #         key="memory_store",
    #         # label_visibility="collapsed",
    #         help="Choose the memory store to use.",
    #     )
    #     chat_agent.memory_store = selected_memory_store
    # chat_agent.profile = chat.get_profile(selected_profile)

    return agent_engine
