import pytest
import hammurabi.utils.product as product


def test_get_version_string_returns_valid_version_string():
    # Act
    version = product.get_version_string()

    # Assert
    assert len(version) > 0
    assert len(version.split(".")) == 3


def test_get_banner_returns_non_empty_banner():
    # Act
    banner = product.get_banner()

    # Assert
    assert isinstance(banner, list)
    assert len(banner) > 0
    assert not any([len(line) > product._terminal_width for line in banner])
