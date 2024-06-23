import pytest

from nexus.nexus_base.nexus import Nexus
from nexus.nexus_base.nexus_models import Agent
from nexus.nexus_base.nexus_planners.basic_nexus_planner import BasicNexusPlanner
from nexus.nexus_base.planner_manager import Plan


@pytest.fixture
def nexus_planner():
    return BasicNexusPlanner()


@pytest.fixture
def nexus():
    return Nexus()


@pytest.fixture
def mock_agent(mocker):
    mock_agent = mocker.create_autospec(Agent)
    mock_agent.id = 1
    mock_agent.name = "Test Agent"
    mock_agent.instructions = "Test instructions"
    mock_agent.engine = "OpenAIAgentEngine"
    mock_agent.engine_settings = {
        "model": "gpt-4o",
        "temperature": 0.0,
        "max_tokens": 1024,
        "top_p": 1.0,
    }
    mock_agent.actions = ["search_wikipedia", "get_wikipedia_page", "save_file"]
    mock_agent.memory = "Test memory"
    mock_agent.knowledge = "Test knowledge"
    mock_agent.evaluation = "Test evaluation"
    mock_agent.feedback = "Test feedback"
    mock_agent.reasoning = "Test reasoning"
    mock_agent.planning = "Test planning"
    mock_agent.thought_template = "Test thought template"
    return mock_agent


def test_create_plan(nexus, mock_agent, nexus_planner):
    goal = "Search wikipedia for pages on Calgary, summarize each page and save all the pages content to a file."

    plan = nexus_planner.create_plan(nexus, mock_agent, goal=goal)

    assert isinstance(plan, Plan)
    assert plan.goal == goal
    assert plan.generated_plan is not None


def test_create_and_execute_plan(nexus, mock_agent, nexus_planner):
    goal = "Search wikipedia for pages on Calgary, summarize each page and save all the pages content to a file."

    plan = nexus_planner.create_plan(nexus, mock_agent, goal=goal)
    output = nexus_planner.execute_plan(nexus, plan)

    assert output is not None
    # assert output["status"] == "success"
    # assert output["result"] is not None
    # assert output["result"]["content"] is not None
    # assert output["result"]["content"]["page_title"] == "Calgary"
    # assert output["result"]["content"]["page_content"] is not None
