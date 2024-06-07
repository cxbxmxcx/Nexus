import pandas as pd
import pytest

from nexus.nexus_base.tracking_manager import TrackingManager


@pytest.fixture
def tm():
    # Create an instance of ChatSystem for testing
    return TrackingManager()


def test_tm_get_next_id(tm):
    # Test the get_next_id method
    id = tm.get_next_id()
    assert id > 0


def test_get_tracking_usage(tm):
    data = tm.get_tracking_usage()
    df = pd.DataFrame(data)

    df.to_csv("data.csv")

    assert df is not None
