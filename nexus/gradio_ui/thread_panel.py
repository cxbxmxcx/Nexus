from functools import partial

import gradio as gr


# Gradio function to load messages for a specific thread
def load_messages(thread_id, nexus):
    # time.sleep(1)
    messages = nexus.read_messages(thread_id)

    def truncate(content, length=40):
        if len(content) > length:
            return content[:length] + "..."
        return content

    def format_message(msg):
        truncated_content = truncate(msg.content)
        return f"<details><summary>{msg.role}: {truncated_content}</summary><p>{msg.content}</p></details>"

    formatted_messages = [format_message(msg) for msg in messages]
    return (
        gr.update(choices=list(load_threads(nexus)), value=thread_id),
        thread_id,
        "\n".join(formatted_messages),
    )


# Function to handle thread selection
def select_thread(thread_id, nexus):
    if thread_id != "new_thread":
        _, _, messages = load_messages(thread_id, nexus)
        return thread_id, messages
    return thread_id, ""


def load_threads(nexus):
    threads = nexus.get_all_threads()
    threads = [(thread.title, thread.thread_id) for thread in threads]
    return threads


def create_new_thread(username, nexus):
    thread = nexus.create_thread("New thread", username, type="agent")
    return (
        gr.update(choices=list(load_threads(nexus)), value=thread.thread_id),
        thread.thread_id,
        "",
    )


# Creating the Gradio interface for the thread panel
def thread_panel(nexus, username):
    with gr.Blocks() as panel:
        threads = load_threads(nexus)
        selected_thread = gr.State()

        with gr.Column():
            new_thread_btn = gr.Button("Create New Thread")

            thread_dropdown = gr.Dropdown(
                label="Select Thread",
                choices=threads,
            )
            message_box = gr.Markdown(
                label="Message History",
                value="",
                elem_id="messagebox",
            )

            thread_dropdown.change(
                partial(select_thread, nexus=nexus),
                inputs=[thread_dropdown],
                outputs=[selected_thread, message_box],
            )

            new_thread_btn.click(
                partial(create_new_thread, nexus=nexus),
                inputs=[username],
                outputs=[
                    thread_dropdown,
                    selected_thread,
                    message_box,
                ],
            )

            notify = gr.Textbox("Notify", visible=False)

            notify.change(
                partial(load_messages, nexus=nexus),
                inputs=[selected_thread],
                outputs=[thread_dropdown, selected_thread, message_box],
            )

    return selected_thread, notify


# # Usage
# nexus = YourNexusClass()  # Replace with your actual nexus instance
# username = "your_username"  # Replace with your actual username
# thread_panel(nexus, username).launch()
