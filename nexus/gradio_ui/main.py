import os
import queue
import re
import threading
import time
from contextlib import contextmanager

import gradio as gr

from nexus.gradio_ui.agents_panel import agents_panel
from nexus.gradio_ui.gradio_logging import Logger
from nexus.gradio_ui.thread_panel import thread_panel
from nexus.nexus_base.global_values import GlobalValues
from nexus.nexus_base.nexus import Nexus

# from playground.actions_manager import ActionsManager
# from playground.assistants_api import api
# from playground.assistants_panel import assistants_panel
# from playground.assistants_utils import EventHandler, get_tools
# from playground.environment_manager import EnvironmentManager
# from playground.semantic_manager import SemanticManager
# from playground.constants import ASSISTANTS_WORKING_FOLDER

# thread = api.create_thread()  # create a new thread everytime this is run
# actions_manager = ActionsManager()
# semantic_manager = SemanticManager()

# # create code environment
# env_manager = EnvironmentManager()
# env_manager.install_requirements()

logger = Logger("logs.txt")
logger.reset_logs()

nexus = Nexus()


def wrap_latex_with_markdown(text):
    # system = """You are a LaTeX genius and equation genius!,
    # Your job is to identify LaTeX and equations in the text.
    # For each block of LaTeX or equation text you will wrap it with $ if the block is inline,
    # or with $$ if the block is on its own line.
    # Examples:
    # inline x^2 + y^2 = z^2 with text -> inline $x^2 + y^2 = z^2$ with text
    # x^2 + y^2 = z^2 -> $$x^2 + y^2 = z^2$$
    # """
    # user = text
    # text = semantic_manager.get_semantic_response(system, user)
    # return text
    # Regular expression to find LaTeX enclosed in [] or ()
    bracket_pattern = re.compile(r"\[(.*?)\]")
    parenthesis_pattern = re.compile(r"\((.*?)\)")

    # Replace LaTeX within brackets with Markdown inline math
    text = bracket_pattern.sub(r"$$\1$$", text)

    # Replace LaTeX within parentheses with Markdown inline math
    text = parenthesis_pattern.sub(r"$$\1$$", text)
    return text


def print_like_dislike(x: gr.LikeData):
    print(x.index, x.value, x.liked)


def ask_agent(agent_id, thread_id, history, message):
    agent = nexus.get_agent(agent_id)
    if agent is None:
        history.append((None, "Agent not found."))
        return history, gr.MultimodalTextbox(value=None, interactive=False)

    if history is None:
        history = []

    attachments = []
    content = ""
    for file in message["files"]:
        with open(file, "r") as f:
            file_content = f.read()
        file = os.path.basename(file)
        file_path = os.path.join(GlobalValues.AGENTS_WORKING_FOLDER, file)
        with open(file_path, "w") as file:
            file.write(file_content)
            attachments = None
        history.append((f"file {file}, saved to working folder.", None))

    if message["text"] is not None:
        history.append((message["text"], None))
        content = message["text"]
    # if content or attachments:  # only create a message if there is content
    #     api.create_thread_message(thread.id, "user", content, attachments=attachments)
    if content:
        nexus.post_message(thread_id, username, role="user", content=content)

    return history, gr.MultimodalTextbox(value=None, interactive=False)


@contextmanager
def dummy_stream(*args, **kwargs):
    yield ["streaming data"]


def extract_file_paths(text):
    # Regular expression pattern to match file paths
    # This pattern matches typical file paths in Windows and Unix-like systems
    pattern = r"(?:[a-zA-Z]:\\)?(?:[a-zA-Z0-9_-]+\\)*[a-zA-Z0-9_-]+\.[a-zA-Z0-9]+|(?:\/[a-zA-Z0-9_-]+)+\/?"

    # Find all matching file paths in the text
    file_paths = re.findall(pattern, text)

    unique_file_paths = list(set(file_paths))

    return unique_file_paths


def get_file_path(file):
    if os.path.isabs(file):
        return file

    file_path = os.path.join(GlobalValues.AGENTS_WORKING_FOLDER, file)
    return file_path


class StreamContextManager:
    def __init__(self, nexus, thread_id, agent):
        self.nexus = nexus
        self.thread_id = thread_id
        self.agent = agent
        self.generator = None

    def __enter__(self):
        self.generator = self.nexus.run_stream(self.thread_id, self.agent)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.generator = None

    @property
    def text_deltas(self):
        if self.generator:
            for partial_message in self.generator:
                yield partial_message


def run(history, agent_id, thread_id):
    output_queue = queue.Queue()
    # eh = EventHandler(output_queue)
    agent = nexus.get_agent(agent_id)

    if agent is None:
        msg = "Assistant not found."
        history.append((None, msg))
        yield history
        return
    if thread_id is None:
        msg = "Thread not found."
        history.append((None, msg))
        yield history
        return

    def stream_worker(agent, thread_id):
        with StreamContextManager(nexus, thread_id, agent) as stream:
            for text in stream.text_deltas:
                output_queue.put(("text", text))
        # with nexus.run_stream(
        #     thread_id=thread_id,
        #     agent=agent,
        # ) as stream:
        #     for text in stream.text_deltas:
        #         output_queue.put(("text", text))

    initial_thread = threading.Thread(target=stream_worker, args=(agent, thread_id))
    initial_thread.start()
    history[-1][1] = ""
    while initial_thread.is_alive() or not output_queue.empty():
        try:
            item_type, item_value = output_queue.get(timeout=0.1)
            if item_type == "text":
                history[-1][1] = item_value
                # history[-1][1] = wrap_latex_with_markdown(history[-1][1])
            yield history

        except queue.Empty:
            pass
    # history[-1][1] = wrap_latex_with_markdown(history[-1][1])
    yield history

    files = extract_file_paths(history[-1][1])
    for file in files:
        file_path = get_file_path(file)
        if os.path.exists(file_path):
            history.append((None, (file_path,)))
        yield history

    # Final flush of images
    # while len(eh.images) > 0:
    #     history.append((None, (eh.images.pop(),)))
    #     yield history

    initial_thread.join()
    nexus.post_message(
        thread_id, agent.agent_id, role="assistant", content=history[-1][1]
    )
    return None


# Custom CSS
custom_css = """
:root {
    --adjustment-ratio: 225px; /* Height to subtract from the viewport for chatbot */
}

body, html {
    height: 100%;
    width: 100%;
    margin: 0;
    padding: 0;
}

.gradio-container {
    max-width: 100% !important; 
    width: 100%;
}

#chatbot {
    height: calc(100vh - var(--adjustment-ratio)) !important; /* Uses adjustment ratio */
    overflow-y: auto !important;
}

#messagebox {
    height: calc(100vh - var(--adjustment-ratio) - 240) !important; /* Uses adjustment ratio */
    overflow-y: auto !important;
}

#instructions textarea {
    min-height: calc(100vh - (var(--adjustment-ratio) + 750px)); /* Additional subtraction to account for other elements */
    max-height: 1000px;
    resize: vertical;
    overflow-y: auto;
}
#assistant_logs textarea {
    height: calc(100vh - (var(--adjustment-ratio) - 25px)); /* Initial height calculation */
    min-height: 150px; /* Set a reasonable min-height */
    max-height: 1000px; /* Max height of 1000px */
    resize: vertical; /* Allow vertical resizing only */
    overflow-y: auto; /* Enable vertical scrollbar when content exceeds max-height */
    box-sizing: border-box; /* Ensure padding and border are included in the height calculation */
}

#actionsnew { 
    color: #000000; 
 }

#actions { 
    color: #000000; 
 }
 
#username span {
     position: absolute;     
     right: 0;
     z-index: 1000;
}
 
video {
    width: 300px;  /* initial width */
    height: 200px; /* initial height */
    transition: width 0.5s ease, height 0.5s ease;
    cursor: pointer;
}
video:hover {
    width: auto;
    height: auto;
    max-width: 100%; /* ensures it doesn’t exceed the container's width */
}
"""


def update_message(request: gr.Request):
    username = request.username
    return username, f"### Welcome, {username}"


theme = "default"

with gr.Blocks(css=custom_css, theme=theme) as demo:
    username_display = gr.Markdown("", elem_id="username")
    username = gr.Markdown("", visible=False)

    with gr.Tab(label="Agent Playground"):
        with gr.Row():
            with gr.Column(scale=2):
                agent_id = agents_panel(nexus)

            with gr.Column(scale=8):
                chatbot = gr.Chatbot(
                    [],
                    elem_id="chatbot",
                    bubble_full_width=True,
                    container=True,
                    avatar_images=["avatar1.png", "avatar2.png"],
                    layout="panel",
                )

                chat_input = gr.MultimodalTextbox(
                    interactive=True,
                    file_types=["image"],
                    placeholder="Enter message or upload file...",
                    show_label=False,
                    elem_id="chat_input",
                )

                chatbot.like(print_like_dislike, None, None)

            with gr.Column(scale=2):
                thread_id, notify = thread_panel(nexus, username)

    with gr.Tab(label="Logs"):
        with gr.Column(scale=4):
            # Add logs
            logs = gr.Code(
                label="", language="python", interactive=False, container=True, lines=45
            )
            demo.load(logger.read_logs, None, logs, every=1)
            demo.load(update_message, None, [username, username_display])

    chat_msg = chat_input.submit(
        ask_agent,
        [agent_id, thread_id, chatbot, chat_input],
        [chatbot, chat_input],
    )
    bot_msg = chat_msg.then(
        run,
        [chatbot, agent_id, thread_id],
        [chatbot],
        api_name="agent_response",
    )
    after_msg = bot_msg.then(
        lambda: gr.MultimodalTextbox(interactive=True), None, [chat_input]
    )

    def notify_input(input):
        return str(time.time())

    after_msg.then(notify_input, chat_input, [notify])

demo.queue()


def authentication(username, password):
    user = nexus.get_participant(username)
    if user:
        if nexus.login(username, password):
            return True
        else:
            return False
    else:
        # Add new user
        nexus.add_participant(username, password, username)
        nexus.login(username, password)
        return True


if __name__ == "__main__":
    demo.launch(
        auth=authentication,
        inbrowser=True,
    )
    # use the following to launch in browser with a shareable link
    # demo.launch(share=True, inbrowser=True)
