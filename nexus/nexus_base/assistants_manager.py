from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class AssistantsManager:
    def __init__(self):
        self.client = OpenAI()

    def create_assistant(self, name, instructions, model, tools):
        assistant = self.client.beta.assistants.create(
            name=name, instructions=instructions, tools=tools, model=model
        )
        return assistant

    def list_assistants(self):
        assistants = self.client.beta.assistants.list()
        return assistants

    def retrieve_assistant(self, assistant_id):
        assistant = self.client.beta.assistants.retrieve(assistant_id)
        return assistant

    def update_assistant(self, assistant_id, name, instructions, model, tools):
        assistant = self.client.beta.assistants.update(
            assistant_id, name=name, instructions=instructions, model=model, tools=tools
        )
        return assistant

    def delete_assistant(self, assistant_id):
        self.client.beta.assistants.delete(assistant_id)

    def get_thread(self, thread_id):
        thread = self.client.beta.threads.retrieve(thread_id)
        return thread

    def create_thread(self):
        thread = self.client.beta.threads.create()
        return thread

    def stream_response(self, thread_id, assistant_id, content):
        message = self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=content,
        )

        with self.client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=assistant_id,
            # event_handler=EventHandler(),
        ) as stream:
            for text in stream.text_deltas:
                yield text
