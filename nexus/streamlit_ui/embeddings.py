from collections import defaultdict

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

from nexus.streamlit_ui.options import create_options_ui


def group_items_by_labels(items, labels):
    """
    Groups items by labels.

    Parameters:
    - items: A list of memory/knowledge items.
    - labels: A list of labels corresponding to each item group.

    Returns:
    A defaultdict with labels as keys and lists of corresponding memories as values.
    """
    grouped_items = defaultdict(list)
    for emb, label in zip(items, labels):
        grouped_items[label].append(emb)
    return grouped_items


def display_items_per_label(grouped_items):
    """
    Displays the number of items per label in a Streamlit table.

    Parameters:
    - grouped_items: A defaultdict with labels as keys and lists of test items as values.
    """
    # Calculating the number of items per label
    label_counts = {label: len(items) for label, items in grouped_items.items()}

    # Converting to a DataFrame for nicer display in Streamlit
    import pandas as pd

    label_counts_df = pd.DataFrame(
        list(label_counts.items()), columns=["Label", "Number of Items"]
    )

    # Displaying the DataFrame as a table in Streamlit
    st.table(label_counts_df.sort_values(by="Number of Items", ascending=False))


def get_agent(chat, agent_key, store_type="memory"):
    agents = chat.get_agent_names()
    if store_type == "knowledge":
        agents = [agent for agent in agents if chat.get_agent(agent).supports_knowledge]
    elif store_type == "memory":
        agents = [agent for agent in agents if chat.get_agent(agent).supports_memory]
    else:
        st.error("Invalid store type. Please choose 'knowledge' or 'memory'.")
        st.stop()
    agent_key = agent_key + store_type
    selected_agent = st.selectbox(
        "Choose an agent engine:",
        agents,
        key=agent_key + "agent",
        # label_visibility="collapsed",
        help=f"Choose an agent to manage {store_type} with.",
    )
    chat_agent = chat.get_agent(selected_agent)
    with st.expander("Agent Options:", expanded=False):
        options = chat_agent.get_attribute_options()
        if options:
            selected_options = create_options_ui(options, agent_key)
            for key, value in selected_options.items():
                setattr(chat_agent, key, value)
    return chat_agent


def view_embeddings(chat, item_store_name, store_type="memory"):
    """
    Displays all memories/knowledge and their embeddings from ChromaDB, colored by KMeans clusters.
    Finds the optimum number of clusters based on silhouette scores for 2 to 20 clusters,
    with a preference for smaller, more numerous clusters.
    """
    if item_store_name is None:
        st.error("Please create a memory store first.")
        st.stop()

    if store_type == "knowledge":
        items = chat.get_documents(item_store_name, include=["documents", "embeddings"])
    elif store_type == "memory":
        items = chat.get_memories(item_store_name, include=["documents", "embeddings"])

    embeddings = items["embeddings"]
    items = items["documents"]

    if embeddings and items and len(embeddings) > 3:
        # Applying PCA to reduce dimensions to 3
        pca = PCA(n_components=3)
        reduced_embeddings = pca.fit_transform(embeddings)

        # Find the optimum number of clusters using silhouette scores
        silhouette_scores = []
        for n_clusters in range(2, 21):  # Test from 2 to 20 clusters
            if n_clusters >= len(reduced_embeddings):
                break
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(reduced_embeddings)
            score = silhouette_score(reduced_embeddings, labels)
            silhouette_scores.append(score)

        # You might prefer more clusters, so instead of directly choosing the highest score,
        # consider a point where adding more clusters doesn't significantly improve the score
        # This is a simplified approach to prioritize more, smaller clusters
        n_clusters_optimal = (
            np.argmax(silhouette_scores) + 2
        )  # Adding 2 because range starts at 2

        # Now that we have our optimal number of clusters, run KMeans with it
        kmeans_optimal = KMeans(n_clusters=n_clusters_optimal, random_state=42)
        kmeans_optimal.fit(reduced_embeddings)
        labels_optimal = kmeans_optimal.labels_

        # Creating a 3D plot using Plotly with data colored by optimal cluster assignment
        fig = go.Figure(
            data=[
                go.Scatter3d(
                    x=reduced_embeddings[:, 0],
                    y=reduced_embeddings[:, 1],
                    z=reduced_embeddings[:, 2],
                    mode="markers",
                    text=items,  # Adding document texts for hover
                    hoverinfo="text",  # Showing only the text on hover
                    marker=dict(
                        size=12,
                        color=labels_optimal,  # Color by cluster labels
                        colorscale="Viridis",  # You can choose any colorscale
                        opacity=0.8,
                    ),
                )
            ],
            layout=dict(
                title=f"Document Embeddings Colored by KMeans Clusters (Optimal Clusters: {n_clusters_optimal})",
                scene=dict(
                    xaxis_title="PCA 1",
                    yaxis_title="PCA 2",
                    zaxis_title="PCA 3",
                ),
                height=800,
            ),
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            st.plotly_chart(fig)

        with col2:
            # Group embeddings by labels using the provided function
            st.header(f"Manage and Compress {store_type.capitalize()} Embeddings")
            grouped_items = group_items_by_labels(items, labels_optimal)
            chat_agent = get_agent(chat, "embed")
            display_items_per_label(grouped_items)
            st.write(
                "Consider using the agent to compress if you have more than 10 items in a cluster."
            )
            if st.button("Compress"):
                with st.spinner(
                    text=f"The agent is compressing {store_type}_{item_store_name}..."
                ):
                    if store_type == "knowledge":
                        chat.compress_knowledge(
                            item_store_name, grouped_items, chat_agent
                        )
                        st.success(f"{store_type} compressed successfully!")
                        st.rerun()
                    elif store_type == "memory":
                        chat.compress_memories(
                            item_store_name, grouped_items, chat_agent
                        )
                        st.success(f"{store_type} compressed successfully!")
                        st.rerun()
                    else:
                        st.error(
                            "Invalid store type. Please choose 'knowledge' or 'memory'."
                        )

    else:
        st.error("Not enough memories to display.")
