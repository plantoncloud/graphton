"""Basic import tests for Graphton package."""


def test_graphton_import() -> None:
    """Test that graphton package can be imported."""
    import graphton

    assert graphton.__version__ == "0.1.0"


def test_core_import() -> None:
    """Test that graphton.core can be imported."""
    from graphton import core

    assert core is not None


def test_utils_import() -> None:
    """Test that graphton.utils can be imported."""
    from graphton import utils

    assert utils is not None












