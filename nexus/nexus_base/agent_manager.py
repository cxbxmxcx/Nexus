import functools
import importlib.util
import os


class BaseAgent:
    _supports_actions = False
    _supports_memory = False
    _supports_knowledge = False

    def __init__(self, chat_history=None):
        self._chat_history = chat_history or []
        self.last_message = ""
        self._actions = []
        self._profile = None
        self.attribute_options = {}

    def add_attribute_options(self, name, details):
        """Add or update an attribute with its details."""
        self.attribute_options[name] = details

    def get_attribute_option(self, name):
        """Get options or constraints for a given attribute."""
        return self.attribute_options.get(name, None)

    def get_attribute_options(self):
        """Get all attribute options."""
        return self.attribute_options

    async def get_response(self, user_input, thread_id=None):
        # Placeholder method to be implemented by subclasses
        raise NotImplementedError("This method should be implemented by subclasses.")

    async def get_semantic_response(self, prompt, thread_id=None):
        # Placeholder method to be implemented by subclasses
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_response_stream(self, user_input, thread_id=None):
        # Placeholder method for streaming responses, to be implemented by subclasses
        raise NotImplementedError("This method should be implemented by subclasses.")

    def append_chat_history(self, thread_id, user_input, response):
        # Method to append user input and bot response to the chat history
        self._chat_history.append(
            {"role": "user", "content": user_input, "thread_id": thread_id}
        )
        self._chat_history.append(
            {"role": "bot", "content": response, "thread_id": thread_id}
        )

    def load_chat_history(self):
        # Placeholder method to load and format chat history for the specific tool
        raise NotImplementedError("This method should be implemented by subclasses.")

    def load_actions(self):
        # Placeholder method to load and format actions for the specific tool
        raise NotImplementedError("This method should be implemented by subclasses.")

    @property
    def chat_history(self):
        return self._chat_history

    # define the setter method
    @chat_history.setter
    def chat_history(self, chat_history):
        self._chat_history = chat_history
        self.load_chat_history()

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, actions):
        self._actions = actions
        self.load_actions()

    @property
    def name(self):
        # Property to get the name of the agent
        return self.__class__.__name__

    @property
    def profile(self):
        return self._profile

    @profile.setter
    def profile(self, profile):
        self._profile = profile

    @classmethod
    def get_supports_actions(cls):
        return cls._supports_actions

    @property
    def supports_actions(self):
        return self.get_supports_actions()

    @classmethod
    def get_supports_memory(cls):
        return cls._supports_memory

    @property
    def supports_memory(self):
        return self.get_supports_memory()

    @classmethod
    def get_supports_knowledge(cls):
        return cls._supports_knowledge

    @property
    def supports_knowledge(self):
        return self.get_supports_knowledge()


def get_nested_attr(obj, attr_path):
    """
    Safely retrieves a nested attribute using a dot-separated path.
    """
    current = obj
    for attr in attr_path.split("."):
        try:
            current = getattr(current, attr)
        except AttributeError:
            return None
    return current


class AgentManager:
    def __init__(self, tracking_manager=None):
        agent_directory = os.path.join(os.path.dirname(__file__), "nexus_agents")
        self.agents = self._load_agents(agent_directory)
        self.tracking_manager = tracking_manager
        if self.tracking_manager:
            self.track_agents(self.agents)

    def get_agent(self, agent_name):
        for agent in self.agents:
            if agent.name == agent_name:
                return agent
        return None

    def track_agents(self, agents):
        for agent in agents:
            self.track_agent_client(agent)

    def track_agent_client(self, agent):
        client = agent.client
        create_path = "chat.completions.create"  # Default path for OpenAI style client
        messages_path = "messages.create"  # Default path for Anthropic style client

        # Get the method for chat.completions.create if it exists
        chat_create_method = get_nested_attr(client, create_path)
        if chat_create_method:
            # Patching OpenAI style client
            setattr(
                client.chat.completions,
                "create",
                functools.partial(
                    self.tracking_manager.track_chat_create(
                        chat_create_method, agent.name
                    ),
                    client.chat.completions,
                ),
            )

        # Get the method for messages.create if it exists
        messages_create_method = get_nested_attr(client, messages_path)
        if messages_create_method:
            # Patching Anthropic style client
            setattr(
                client.messages,
                "create",
                functools.partial(
                    self.tracking_manager.track_messages_create(
                        messages_create_method, agent.name
                    ),
                    client.messages,
                ),
            )

    def get_agent_names(self):
        return [agent.name for agent in self.agents]

    def _load_agents(self, agent_directory):
        agents = []
        for filename in os.listdir(agent_directory):
            if filename.endswith(".py") and not filename.startswith("_"):
                try:
                    module_name = filename[:-3]
                    module_path = os.path.join(agent_directory, filename)
                    spec = importlib.util.spec_from_file_location(
                        module_name, module_path
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    for attribute_name in dir(module):
                        attribute = getattr(module, attribute_name)
                        if (
                            isinstance(attribute, type)
                            and issubclass(attribute, BaseAgent)
                            and attribute is not BaseAgent
                        ):
                            agents.append(attribute())
                except Exception as e:
                    print(f"Error loading agent from {filename}: {e}")
        return agents
