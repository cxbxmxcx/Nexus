import pytest

from nexus.nexus_base.agent_manager import AgentManager


@pytest.fixture
def am():
    return AgentManager()


def test_create_agent(am):
    agent = am.create_agent("test_agent")
    assert agent is not None


def test_get_agents(am):
    agents = am.get_agents()
    assert agents is not None
