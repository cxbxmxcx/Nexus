import os

from dotenv import load_dotenv
from groq import Groq

from nexus.nexus_base.agent_manager import BaseAgent
from nexus.nexus_base.nexus_models import Message

load_dotenv()  # loading and setting the api key can be done in one step


class GroqAgent(BaseAgent):
    _supports_actions = False
    _supports_knowledge = True
    _supports_memory = True

    def __init__(self, chat_history=None):
        super().__init__(chat_history)
        self.last_message = ""
        self._chat_history = chat_history
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.client.models.list()
        self.model = "mixtral-8x7b-32768"

        self.max_tokens = 1024
        self.temperature = 0.7
        self.messages = []  # history of messages
        self.tools = []

        self.add_attribute_options(
            "model",
            {
                "type": "string",
                "default": "mixtral-8x7b-32768",
                "options": [
                    "mixtral-8x7b-32768",
                    "gemma-7b-it",
                    "llama2-70b-4096",
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
        self.messages += [{"role": "user", "content": user_input}]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
        )
        self.last_message = str(response)
        return str(response)

    def get_semantic_response(self, system, user):
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        # how can I capture response.usage or the whole response object?
        return str(response.choices[0].message.content)

    def get_response_stream(self, user_input, thread_id=None):
        self.last_message = ""
        self.messages += [{"role": "user", "content": user_input}]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
        )
        response_message = response.choices[0].message
        self.last_message = str(response_message.content)

        def generate_responses():
            response = self.last_message
            for character in response:
                yield character

        return generate_responses

    def append_message(self, message: Message):
        if message.role == "agent":
            self.messages.append(dict(role="assistant", content=message.content))
        else:
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
            self.messages.append({"role": "system", "content": self._profile.persona})
