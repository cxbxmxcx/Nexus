import pandas as pd
import plotly.express as px
import streamlit as st

from nexus.streamlit_ui.cache import get_nexus


def usage_page(username, win_height):
    chat = get_nexus()
    user = chat.get_participant(username)
    if user is None:
        st.error("Invalid user")
        st.stop()

    data = chat.get_tracking_usage()
    df = pd.DataFrame(data)

    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    # Calculate total tokens
    df["total_tokens"] = df["in_tokens"] + df["out_tokens"]

    # # Group by model, function, tracking_id, and name and sum the total tokens
    # grouped_data = (
    #     df.groupby(["model", "function", "tracking_id", "name"])["total_tokens"]
    #     .sum()
    #     .reset_index()
    # )
    # # Create the first interactive plot
    # fig1 = px.bar(
    #     grouped_data,
    #     x="model",
    #     y="total_tokens",
    #     color="function",
    #     hover_data=["tracking_id", "name"],
    # )
    # fig1.update_layout(
    #     title="Total Token Usage by Model, Function, Tracking ID, and Name"
    # )

    # # Streamlit layout
    # st.header("Agent Usage Statistics")
    # st.write("## Total Token Usage by Model, Name, Function, and Tracking ID")
    # st.plotly_chart(fig1)

    # 1. Token Efficiency Plot
    token_efficiency_fig = px.scatter(
        df,
        x="total_tokens",
        y="elapsed_time",
        color="model",
        labels={"in_tokens": "Input Tokens", "out_tokens": "Output Tokens"},
        title="Token Efficiency Plot",
        width=1024,
    )

    # 2. Function Usage Frequency
    function_usage_fig = px.histogram(
        df,
        x="function",
        color="model",
        title="Function Usage Frequency",
        width=1024,
    )

    # 3. Function Token Usage
    time_series_tokens_fig = px.histogram(
        df,
        x="total_tokens",
        y=["tracking_id", "function"],
        color="model",
        labels={"value": "Token Count", "variable": "Token Type"},
        title="Token Usage by Function and Tracking ID",
        width=1024,
    )

    # 4. Elapsed Time Analysis
    # Note: All elapsed_time values are zero, making this plot less informative but still creating for demonstration
    elapsed_time_fig = px.box(
        df,
        y="elapsed_time",
        color="function",
        title="Elapsed Time Analysis",
        width=1024,
    )

    # 5. Heatmap of Token Usage by Hour of Day
    df["hour"] = df["timestamp"].dt.hour
    heatmap_data = (
        df.groupby("hour").agg({"in_tokens": "sum", "out_tokens": "sum"}).reset_index()
    )
    heatmap_fig = px.density_contour(
        df,
        x="in_tokens",
        y="elapsed_time",
        z="total_tokens",
        color="model",
        labels={"value": "Token Count"},
        title="Heatmap of Token Usage by Hour of Day",
        width=1024,
    )

    # 6. Cross-Model Comparison
    cross_model_fig = px.area(
        df,
        x="elapsed_time",
        y="total_tokens",
        color="model",
        title="Total Token Comparison",
        width=1024,
    )

    # Displaying plots
    st.plotly_chart(token_efficiency_fig)
    st.plotly_chart(function_usage_fig)
    st.plotly_chart(time_series_tokens_fig)
    st.plotly_chart(elapsed_time_fig)
    st.plotly_chart(heatmap_fig)
    st.plotly_chart(cross_model_fig)
