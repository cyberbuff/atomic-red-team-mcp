"""Tests for output schema models."""

from atomic_red_team_mcp.models import (
    MetaAtomic,
    QueryAtomicsOutput,
    RefreshAtomicsOutput,
    ServerInfoOutput,
    ValidationOutput,
)


def test_query_atomics_output():
    """Test QueryAtomicsOutput model."""
    output = QueryAtomicsOutput(
        total_results=10,
        atomics=[],
        next_cursor="opaque-cursor-string",
        query_metadata={"query": "test"},
    )

    assert output.total_results == 10
    assert output.next_cursor == "opaque-cursor-string"


def test_query_atomics_output_no_more():
    """Test QueryAtomicsOutput when no more results."""
    output = QueryAtomicsOutput(
        total_results=5,
        atomics=[],
        next_cursor=None,
        query_metadata={},
    )

    assert output.next_cursor is None


def test_validation_output_success():
    """Test ValidationOutput for successful validation."""
    output = ValidationOutput(
        valid=True,
        message="Success",
        atomic_name="Test Atomic",
        supported_platforms=["windows"],
    )

    assert output.valid
    assert output.atomic_name == "Test Atomic"
    assert output.error is None


def test_validation_output_with_warnings():
    """Test ValidationOutput with warnings."""
    output = ValidationOutput(
        valid=True,
        message="Success with warnings",
        atomic_name="Test Atomic",
        supported_platforms=["windows"],
        warnings=["Warning 1", "Warning 2"],
    )

    assert output.valid
    assert len(output.warnings) == 2


def test_validation_output_failure():
    """Test ValidationOutput for failed validation."""
    output = ValidationOutput(
        valid=False, message="Validation failed", error="Missing required field"
    )

    assert not output.valid
    assert output.error is not None
    assert output.atomic_name is None


def test_refresh_atomics_output_success():
    """Test RefreshAtomicsOutput for successful refresh."""
    output = RefreshAtomicsOutput(
        success=True,
        message="Refreshed 100 atomics",
        atomics_count=100,
        repository_url="https://github.com/redcanaryco/atomic-red-team.git",
    )

    assert output.success
    assert output.atomics_count == 100


def test_refresh_atomics_output_failure():
    """Test RefreshAtomicsOutput for failed refresh."""
    output = RefreshAtomicsOutput(
        success=False,
        message="Failed to refresh",
        atomics_count=0,
        repository_url="https://github.com/redcanaryco/atomic-red-team.git",
    )

    assert not output.success
    assert output.atomics_count == 0


def test_server_info_output():
    """Test ServerInfoOutput model."""
    output = ServerInfoOutput(
        name="Atomic Red Team MCP",
        version="1.2.6",
        transport="stdio",
        os="Darwin",
        data_directory="/path/to/atomics",
        execution_enabled=False,
    )

    assert output.name == "Atomic Red Team MCP"
    assert output.version == "1.2.6"
    assert output.transport == "stdio"
    assert not output.execution_enabled


def test_query_atomics_output_with_atomics():
    """Test QueryAtomicsOutput with actual atomic tests."""
    atomic = MetaAtomic(
        name="Test",
        description="Test",
        supported_platforms=["windows"],
        executor={"name": "powershell", "command": "Get-Process"},
        technique_id="T1059.001",
        technique_name="PowerShell",
    )

    output = QueryAtomicsOutput(
        total_results=1,
        atomics=[atomic],
        next_cursor=None,
        query_metadata={},
    )

    assert len(output.atomics) == 1
    assert output.atomics[0].name == "Test"


def test_output_model_serialization():
    """Test that output models can be serialized to dict."""
    output = QueryAtomicsOutput(
        total_results=10,
        atomics=[],
        next_cursor="abc123",
        query_metadata={"query": "test"},
    )

    dict_output = output.model_dump()

    assert dict_output["total_results"] == 10
    assert dict_output["next_cursor"] == "abc123"


def test_validation_output_json_serialization():
    """Test ValidationOutput JSON serialization."""
    output = ValidationOutput(
        valid=True,
        message="Success",
        atomic_name="Test",
        supported_platforms=["windows"],
    )

    json_str = output.model_dump_json()

    assert "valid" in json_str
    assert "true" in json_str.lower()
