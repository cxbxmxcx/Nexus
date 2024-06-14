from nexus.nexus_base.nexus_models import Agent, db
from nexus.nexus_base.utils import id_hash


class AgentManager:
    def __init__(self):
        pass

    def create_agent(self, **kwargs):
        try:
            id = id_hash(kwargs["name"])
            kwargs["agent_id"] = f"agent_{id}"
            kwargs["thought_template"] = (
                None  # Assuming ThoughtTemplate is not implemented yet
            )
            with db.atomic():
                agent = Agent.create(**kwargs)
            return agent
        except Agent.IntegrityError as e:
            print(f"Error creating agent: {e}")
            return None

    def get_agent(self, agent_id):
        try:
            agent = Agent.get(Agent.agent_id == agent_id)
            return agent
        except Agent.DoesNotExist:
            print(f"Agent with ID {agent_id} does not exist.")
            return None

    def get_agent_by_name(self, name):
        try:
            agent = Agent.get(Agent.name == name)
            return agent
        except Agent.DoesNotExist:
            print(f"Agent with name {name} does not exist.")
            return None

    def query_agents(self, **kwargs):
        try:
            agents = Agent.select().where(**kwargs)
            return [agent for agent in agents]
        except Agent.DoesNotExist:
            print(f"Agents with query {kwargs} do not exist.")
            return None

    def update_agent(self, agent_id, **kwargs):
        try:
            with db.atomic():
                agent = Agent.get(Agent.agent_id == agent_id)
                agent.update(**kwargs).where(Agent.agent_id == agent_id).execute()
            return self.get_agent(agent_id)
        except Agent.DoesNotExist:
            print(f"Agent with ID {agent_id} does not exist.")
            return None
        except Exception as e:
            print(f"Error updating agent: {e}")
            return None

    def delete_agent(self, agent_id):
        try:
            with db.atomic():
                agent = Agent.get(Agent.agent_id == agent_id)
                agent.delete_instance()
            return True
        except Agent.DoesNotExist:
            print(f"Agent with ID {agent_id} does not exist.")
            return False

    def list_agents(self):
        agents = Agent.select()
        return [agent for agent in agents]

    def manage_agent(self, agent_id, action, **kwargs):
        """
        Manage an agent by performing specific actions.
        Actions can be: 'create', 'update', 'delete'
        """
        if action == "create":
            return self.create_agent(**kwargs)
        elif action == "update":
            return self.update_agent(agent_id, **kwargs)
        elif action == "delete":
            return self.delete_agent(agent_id)
        elif action == "get":
            return self.get_agent(agent_id)
        else:
            print(f"Invalid action: {action}")
            return None


# # Usage Example
# if __name__ == "__main__":
#     db = SqliteDatabase('agents.db')
#     agent_manager = AgentManager(db)

#     # Create a new agent
#     agent_data = {
#         "agent_id": "001",
#         "name": "Example Agent",
#         "instructions": "Example instructions",
#         "engine": "gpt-3.5",
#         "engine_settings": "{}",
#         "actions": "{}",
#         "memory": "{}",
#         "knowledge": "{}",
#         "evaluation": "{}",
#         "feedback": "{}",
#         "reasoning": "{}",
#         "planning": "{}",
#         "thought_template": 1  # Assuming ThoughtTemplate with ID 1 exists
#     }
#     new_agent = agent_manager.create_agent(**agent_data)
#     print(f"Created agent: {new_agent}")

#     # List all agents
#     agents = agent_manager.list_agents()
#     print(f"Agents: {agents}")
