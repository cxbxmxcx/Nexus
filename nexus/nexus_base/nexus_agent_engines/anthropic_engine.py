import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from nexus.nexus_base.agent_engine_manager import BaseAgentEngine
from nexus.nexus_base.nexus_models import Message

load_dotenv()  # loading and setting the api key can be done in one step


class AnthropicAgentEngine(BaseAgentEngine):
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

        self.add_engine_setting_option(
            "model",
            {
                "type": "string",
                "default": "claude-3-5-sonnet-20240620",
                "options": [
                    "claude-3-5-sonnet-20240620",
                    "claude-3-opus-20240229",
                    "claude-3-sonnect-20240229",
                    "claude-3-haiku-20240307",
                ],
            },
        )
        self.add_engine_setting_option(
            "temperature",
            {
                "type": "numeric",
                "default": 0.7,
                "min": 0.0,
                "max": 1.0,
                "step": 0.1,
            },
        )
        self.add_engine_setting_option(
            "top_p",
            {
                "type": "numeric",
                "default": 1.0,
                "min": 0.0,
                "max": 1.0,
                "step": 0.1,
            },
        )
        self.add_engine_setting_option(
            "max_tokens",
            {
                "type": "numeric",
                "default": 1024,
                "min": 100,
                "max": 8096,
                "step": 10,
            },
        )

    def convert_openai_to_anthropic_schema(self, openai_schema):
        anthropic_schema = []

        for tool in openai_schema:
            if tool["type"] == "function":
                function = tool["function"]
                anthropic_tool = {
                    "name": function["name"],
                    "description": function["description"],
                    "input_schema": {
                        "type": "object",
                        "properties": function["parameters"]["properties"],
                        "required": function["parameters"]["required"],
                    },
                }
                anthropic_schema.append(anthropic_tool)

        return anthropic_schema

    def run_stream(self, system, messages, use_tools=True):
        self.last_message = ""

        if use_tools and len(self.tools) > 0:
            tools = self.convert_openai_to_anthropic_schema(self.tools)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                tools=tools,
                messages=messages,
                system=system,
            )

            while response.stop_reason == "tool_use":
                tool_use = next(
                    block for block in response.content if block.type == "tool_use"
                )
                tool_name = tool_use.name
                tool_input = tool_use.input

                print(f"\nTool Used: {tool_name}")
                print("Tool Input:")
                print(json.dumps(tool_input, indent=2))

                available_tools = {
                    action["name"]: action["pointer"] for action in self.actions
                }

                # tool_result = process_tool_call(tool_name, tool_input)
                action_to_call = available_tools[tool_name]

                print(f"Calling function: {tool_name} with args: {tool_input}")

                tool_result = action_to_call(**tool_input, _caller_agent=self)

                messages += [
                    {"role": "assistant", "content": response.content},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": str(tool_result),
                            }
                        ],
                    },
                ]

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    tools=tools,
                    messages=messages,
                    system=system,
                )

            final_response = next(
                (block.text for block in response.content if hasattr(block, "text")),
                None,
            )

            print(f"Final Response: {final_response}")

            yield final_response

        else:
            stream = self.client.messages.create(
                max_tokens=4096,
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                system=system,
                stream=True,
            )

            def generate_responses():
                for event in stream:
                    if event.type == "content_block_delta":
                        self.last_message += event.delta.text
                        yield self.last_message
                    else:
                        yield self.last_message

            return generate_responses()

    def execute_prompt(self, prompt):
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=prompt,
            messages=[{"role": "user", "content": "run"}],
        )
        return message.content[0].text

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
