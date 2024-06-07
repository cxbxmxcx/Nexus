import json

from dotenv import load_dotenv
from openai import OpenAI

from nexus.nexus_base.agent_manager import BaseAgent
from nexus.nexus_base.nexus_models import Message

load_dotenv()  # loading and setting the api key can be done in one step


class OpenAIAgent(BaseAgent):
    _supports_actions = True
    _supports_knowledge = True
    _supports_memory = True

    def __init__(self, chat_history=None):
        super().__init__(chat_history)
        self.last_message = ""
        self._chat_history = chat_history
        self.client = OpenAI()
        self.client.models.list()
        self.model = "gpt-4-1106-preview"
        self.max_tokens = 1024
        self.temperature = 0.7
        self.messages = []  # history of messages
        self.tools = []

        self.add_attribute_options(
            "model",
            {
                "type": "string",
                "default": "gpt-4-1106-preview",
                "options": [
                    "gpt-4o",
                    "gpt-4-1106-preview",
                    "gpt-3.5-turbo-1106",
                    "gpt-4-0613",
                    "gpt-4",
                    "gpt-4-0125-preview",
                    "gpt-4-turbo-preview",
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
        return str(response.choices[0].message.content)

    def get_response_stream(self, user_input, thread_id=None):
        self.last_message = ""
        self.messages += [{"role": "user", "content": user_input}]
        if self.tools and len(self.tools) > 0:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature,
                tools=self.tools,
                tool_choice="auto",  # auto is default, but we'll be explicit
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        # Step 2: check if the model wanted to call a function
        if tool_calls:
            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors
            available_functions = {
                action["name"]: action["pointer"] for action in self.actions
            }
            self.messages.append(
                response_message
            )  # extend conversation with assistant's reply
            # Step 4: send the info for each function call and function response to the model
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(
                    **function_args, _caller_agent=self
                )

                self.messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(function_response),
                    }
                )  # extend conversation with function response
            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )  # get a new response from the model where it can see the function response
            response_message = second_response.choices[0].message

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
