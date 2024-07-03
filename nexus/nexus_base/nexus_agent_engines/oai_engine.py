import json

from dotenv import load_dotenv
from openai import OpenAI

from nexus.nexus_base.agent_engine_manager import BaseAgentEngine
from nexus.nexus_base.nexus_models import Message

load_dotenv()  # loading and setting the api key can be done in one step


class OpenAIAgentEngine(BaseAgentEngine):
    _supports_actions = True
    _supports_knowledge = True
    _supports_memory = True

    def __init__(self, chat_history=None):
        super().__init__(chat_history)
        self.last_message = ""
        self._chat_history = chat_history
        self.client = OpenAI()
        self.client.models.list()
        self.model = "gpt-4o"
        self.max_tokens = 1024
        self.temperature = 0.7
        self.top_p = 1.0
        self.messages = []  # history of messages
        self.tools = []

        self.add_engine_setting_option(
            "model",
            {
                "type": "string",
                "default": "gpt-4o",
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
        self.add_engine_setting_option(
            "temperature",
            {
                "type": "numeric",
                "default": 0.7,
                "min": 0.0,
                "max": 2.0,
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

    def run_stream(self, system, messages, stream_complete, use_tools=True):
        # Inject system message if present
        if system:
            self.inject_system_message(messages, system)

        # self.last_message = ""
        # self.messages += [{"role": "user", "content": user_input}]

        if use_tools and self.tools and len(self.tools) > 0:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                tools=self.tools,
                tool_choice="auto",  # auto is default, but we'll be explicit
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                stream=True,  # Stream the response
            )

            partial_message = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    partial_message += chunk.choices[0].delta.content
                    yield partial_message
            return  # Exit the function since streaming is complete

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # Check if the model wanted to call a function
        if tool_calls:
            available_functions = {
                action["name"]: action["pointer"] for action in self.actions
            }
            messages.append(
                response_message
            )  # Extend conversation with assistant's reply

            # Call the function(s)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                print(f"Calling function: {function_name} with args: {function_args}")

                function_response = function_to_call(
                    **function_args, _caller_agent=self
                )
                print(f"--- Function response: {function_response}")

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(function_response),
                    }
                )  # Extend conversation with function response

            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )  # Get a new response from the model where it can see the function response
            response_message = second_response.choices[0].message

        last_response = str(response_message.content)
        msg = ""
        # continue_stream = False
        # if "CONTINUE" in last_response:
        #     last_response = last_response.replace("CONTINUE", "")
        #     continue_stream = True

        for character in last_response:
            msg += character
            yield msg

        # if continue_stream:
        #     messages.append({"role": "assistant", "content": last_response})
        #     messages.append({"role": "user", "content": "proceed"})
        #     generator = self.run_stream(None, messages, use_tools)
        #     for response in generator:
        #         yield response
        stream_complete(last_response)
        return

    def execute_prompt(self, prompt):
        messages = [{"role": "system", "content": prompt}]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
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
