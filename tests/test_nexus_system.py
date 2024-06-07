import pytest

from nexus.nexus_base.nexus import Nexus


@pytest.fixture
def nexus():
    # Create an instance of Nexus for testing
    return Nexus()


def test_nexus_get_all_participants(nexus):
    # Test the get_all_participants method
    users = nexus.get_all_participants()
    assert len(users) > 0
