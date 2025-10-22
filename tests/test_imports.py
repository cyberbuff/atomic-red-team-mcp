"""Test that all modules can be imported successfully."""


def test_import_models():
    """Test that models can be imported."""
    from atomic_red_team_mcp.models import Atomic, MetaAtomic, Technique

    assert Atomic is not None
    assert MetaAtomic is not None
    assert Technique is not None


def test_import_services():
    """Test that services can be imported."""
    from atomic_red_team_mcp.services import download_atomics, load_atomics, run_test

    assert download_atomics is not None
    assert load_atomics is not None
    assert run_test is not None


def test_import_tools():
    """Test that tools can be imported."""
    from atomic_red_team_mcp.tools import (
        execute_atomic,
        get_validation_schema,
        query_atomics,
        refresh_atomics,
        server_info,
        validate_atomic,
    )

    assert execute_atomic is not None
    assert get_validation_schema is not None
    assert query_atomics is not None
    assert refresh_atomics is not None
    assert server_info is not None
    assert validate_atomic is not None


def test_import_server():
    """Test that server can be imported."""
    from atomic_red_team_mcp.server import create_mcp_server

    assert create_mcp_server is not None


def test_import_utils():
    """Test that utils can be imported."""
    from atomic_red_team_mcp.utils import get_atomics_dir

    assert get_atomics_dir is not None
