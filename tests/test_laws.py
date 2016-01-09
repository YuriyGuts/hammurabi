import pytest
import hammurabi.utils.laws as laws


def test_get_random_law_returns_law():
    # Act
    law = laws.get_random_law()

    # Assert
    assert isinstance(law, str)
    assert len(law) > 0
