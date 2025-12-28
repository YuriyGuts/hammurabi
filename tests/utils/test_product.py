import shutil

from hammurabi.utils import product


def test_get_version_string_returns_valid_version_string():
    version = product.get_version_string()

    assert len(version) > 0
    assert len(version.split(".")) == 3


def test_get_banner_returns_non_empty_banner():
    banner = product.get_banner()
    terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns

    assert isinstance(banner, list)
    assert len(banner) > 0
    assert all(len(line) <= terminal_width for line in banner)
