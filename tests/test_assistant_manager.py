import pytest

from nexus.nexus_base.assistants_manager import AssistantsManager


@pytest.fixture
def am():
    # Create an instance of Nexus for testing
    return AssistantsManager()


def test_get_threads(am):
    # Test the get_threads method
    threads = am.get_threads()
    assert len(threads) > 0
