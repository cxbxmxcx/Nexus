import streamlit as st

from nexus.nexus_base.nexus_models import MemoryType
from nexus.streamlit_ui.cache import get_nexus
from nexus.streamlit_ui.embeddings import get_agent, view_embeddings


def add_memory_to_store(chat, memory_store):
    if memory_store is None:
        st.error("Please create a memory store first.")
        st.stop()

    chat_agent = get_agent(chat, "add", "memory")

    memory = st.text_area("Enter a memory to add to the store:")

    if st.button("Add Memory") and memory != "" and memory is not None:
        chat.load_memory(memory_store, memory, chat_agent)
        st.success("Memory added successfully!")


def memory_page(username, win_height):
    chat = get_nexus()
    user = chat.get_participant(username)
    if user is None:
        st.error("Invalid user")
        st.stop()

    # Streamlit UI
    st.title("Memory Store Manager")

    with st.sidebar.expander("Manage Memory Stores"):
        store_name = st.text_input("Enter a new memory store name to create:")
        store_name = store_name.strip().replace(" ", "_")
        if st.button(
            "Create Memory Store",
            disabled=(
                store_name == ""
                or store_name in chat.get_memory_store_names()
                or store_name is None
                or len(store_name) < 3
            ),
        ):
            chat.add_memory_store(store_name)
            st.success(f"Memory Store '{store_name}' created!")

        selected_store_to_delete = st.selectbox(
            "Select a memory store to delete:",
            options=list(chat.get_memory_store_names()),
        )
        if st.button("Delete Memory Store"):
            chat.delete_memory_store(selected_store_to_delete)
            st.success(f"Memory Store '{selected_store_to_delete}' deleted!")

    # Memory Management within a Memory Store
    st.header("Manage Memory Store")
    selected_store = st.selectbox(
        "Select a memory store to manage memories:",
        options=list(chat.get_memory_store_names()),
        key="manage_docs",
    )
    st.header(f"Managing {selected_store}")
    config_tabs = st.tabs(
        [
            "Add memories",
            "Examine memories",
            "Memory Embeddings & Compression",
            "Query Memories",
            "Configuration",
        ]
    )

    with config_tabs[0]:
        st.subheader("Add Memory to Memory Store")
        add_memory_to_store(chat, selected_store)

    with config_tabs[1]:
        st.subheader("Examine Memories in Memory Store")
        df = chat.examine_memories(selected_store)
        st.table(df)

    with config_tabs[2]:
        st.subheader("Memory Embeddings and Compression")
        view_embeddings(chat, selected_store, "memory")

    with config_tabs[3]:
        st.subheader("Query Memory Store")
        query = st.text_area("Enter a query to search for similar memories:")
        if st.button("Search"):
            docs = chat.query_memories(selected_store, query)
            for doc in docs:
                st.write(doc)

    with config_tabs[4]:
        st.subheader("Memory Store Configuration")
        memory_store = chat.get_memory_store(selected_store)

        memory_types = [
            MemoryType.CONVERSATIONAL.value,
            MemoryType.SEMANTIC.value,
            MemoryType.PROCEDURAL.value,
            MemoryType.EPISODIC.value,
        ]
        memory_store.memory_type = st.selectbox(
            "Memory Type",
            memory_types,
            index=memory_types.index(memory_store.memory_type),
        )

        memory_function = chat.get_memory_function(memory_store.memory_type)
        st.text_area("Memory Function:", memory_function.function_prompt, disabled=True)
        st.text_area(
            "Augmentation Prompt:", memory_function.augmentation_prompt, disabled=True
        )
        st.text_area(
            "Summarization Prompt:", memory_function.summarization_prompt, disabled=True
        )

        if st.button("Save Configuration"):
            chat.update_memory_store(memory_store)
            st.success("Configuration saved successfully!")
