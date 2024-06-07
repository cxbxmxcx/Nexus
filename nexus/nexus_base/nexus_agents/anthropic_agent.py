import os

from anthropic import Anthropic
from dotenv import load_dotenv

from nexus.nexus_base.agent_manager import BaseAgent
from nexus.nexus_base.nexus_models import Message

load_dotenv()  # loading and setting the api key can be done in one step


class AnthropicAgent(BaseAgent):
    _supports_actions = (
        False  # anthropic tool use is still in alpha, not going to touch it yet
    )
    _supports_knowledge = True
    _supports_memory = True

    def __init__(self, chat_history=None):
        super().__init__(chat_history)
        self.last_message = ""
        self._chat_history = chat_history
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set.")
        self.client = Anthropic()
        self.model = "claude-3-opus-20240229"
        self.max_tokens = 1024
        self.temperature = 0.7
        self.messages = []  # history of messages
        self.tools = []
        self.system = ""

        self.add_attribute_options(
            "model",
            {
                "type": "string",
                "default": "claude-3-opus-20240229",
                "options": [
                    "claude-3-opus-20240229",
                    "claude-3-sonnect-20240229",
                    "claude-3-haiku-20240307",
                ],
            },
        )
        self.add_attribute_options(
            "temperature",
            {
                "type": "numeric",
                "default": 0.7,
                "min": 0.0,
                "max": 1.0,
                "step": 0.1,
            },
        )
        self.add_attribute_options(
            "max_tokens",
            {
                "type": "numeric",
                "default": 1024,
                "min": 100,
                "max": 4096,
                "step": 10,
            },
        )

    async def get_response(self, user_input, thread_id=None):
        return None

    def get_semantic_response(self, system, user):
        messages = [
            {"role": "user", "content": user},
        ]
        response = self.client.messages.create(
            max_tokens=self.max_tokens,
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            system=system,
        )
        return str(response.content[0].text)

    def get_response_stream(self, user_input, thread_id=None):
        self.last_message = ""
        self.messages += [{"role": "user", "content": user_input}]

        stream = self.client.messages.create(
            max_tokens=self.max_tokens,
            messages=self.messages,
            model=self.model,
            temperature=self.temperature,
            system=self.system,
            stream=True,
        )

        def generate_responses():
            for event in stream:
                if event.type == "content_block_delta":
                    self.last_message += event.delta.text
                    yield event.delta.text
                else:
                    yield ""

        return generate_responses

    def append_message(self, message: Message):
        if message.role == "agent":
            message.role = "assistant"

        if len(self.messages) > 0 and self.messages[-1]["role"] == message.role:
            # Anthropic doesn't like it when the same role sends two messages in a row
            return
        self.messages.append(dict(role=message.role, content=message.content))

    def load_chat_history(self):
        self.set_profile()
        if self.chat_history:
            for message in self.chat_history:
                self.append_message(message)

    def load_actions(self):
        self.tools = []
        for action in self.actions:
            self.tools.append(action["agent_action"])

    def set_profile(self):
        if self._profile:
            self.system = self._profile.persona
            self.system = self._profile.persona
