import gradio as gr

streamlit_url = "http://localhost:8501"  # Update this with your Streamlit app's URL

iframe_html = f'<iframe src="{streamlit_url}" width="100%" height="600px"></iframe>'


def greet(name):
    return f"Hello {name}!"


with gr.Blocks() as demo:
    gr.HTML(iframe_html)

demo.launch()
