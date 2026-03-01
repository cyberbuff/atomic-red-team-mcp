"""Tests for execute_atomic tool."""

import json
import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest

from atomic_red_team_mcp.models import CommandExecutor, ExecuteAtomicOutput, MetaAtomic
from atomic_red_team_mcp.tools.execute_atomic import execute_atomic


SAMPLE_GUID = "a8c41029-8d2a-4661-ab83-e5104c1cb667"

SAMPLE_ATOMIC = MetaAtomic(
    name="Test PowerShell",
    description="Test",
    supported_platforms=["windows"],
    executor=CommandExecutor(name="powershell", command="Get-Process"),
    technique_id="T1059.001",
    auto_generated_guid=uuid.UUID(SAMPLE_GUID),
)


@pytest.fixture
def mock_context():
    ctx = Mock()
    ctx.elicit = AsyncMock()
    return ctx


@pytest.mark.anyio
async def test_execute_atomic_guid_not_found(mock_context):
    """Test that a missing GUID returns success=False with an error message."""
    with patch(
        "atomic_red_team_mcp.tools.execute_atomic.load_atomics",
        return_value=[SAMPLE_ATOMIC],
    ):
        result = await execute_atomic(
            mock_context, auto_generated_guid="nonexistent-guid"
        )

    assert isinstance(result, ExecuteAtomicOutput)
    assert result.success is False
    assert "nonexistent-guid" in result.error


@pytest.mark.anyio
async def test_execute_atomic_elicitation_decline(mock_context):
    """Test that declining the GUID prompt returns success=False."""
    elicit_result = Mock()
    elicit_result.action = "decline"
    mock_context.elicit = AsyncMock(return_value=elicit_result)

    result = await execute_atomic(mock_context)

    assert isinstance(result, ExecuteAtomicOutput)
    assert result.success is False
    assert "not provided" in result.error


@pytest.mark.anyio
async def test_execute_atomic_elicitation_cancel(mock_context):
    """Test that cancelling the GUID prompt returns success=False."""
    elicit_result = Mock()
    elicit_result.action = "cancel"
    mock_context.elicit = AsyncMock(return_value=elicit_result)

    result = await execute_atomic(mock_context)

    assert isinstance(result, ExecuteAtomicOutput)
    assert result.success is False
    assert "cancelled" in result.error.lower()


@pytest.mark.anyio
async def test_execute_atomic_json_parse_failure(mock_context):
    """Test that a JSON parse error returns success=False with error detail."""
    with (
        patch(
            "atomic_red_team_mcp.tools.execute_atomic.load_atomics",
            return_value=[SAMPLE_ATOMIC],
        ),
        patch(
            "atomic_red_team_mcp.tools.execute_atomic.run_test",
            return_value="not valid json",
        ),
    ):
        result = await execute_atomic(mock_context, auto_generated_guid=SAMPLE_GUID)

    assert isinstance(result, ExecuteAtomicOutput)
    assert result.success is False
    assert "parse" in result.error.lower()


@pytest.mark.anyio
async def test_execute_atomic_success(mock_context):
    """Test successful execution returns structured output with correct fields."""
    run_output = json.dumps(
        [{"phase": "test", "output": "stdout text", "errors": "", "return_code": 0}]
    )

    with (
        patch(
            "atomic_red_team_mcp.tools.execute_atomic.load_atomics",
            return_value=[SAMPLE_ATOMIC],
        ),
        patch(
            "atomic_red_team_mcp.tools.execute_atomic.run_test",
            return_value=run_output,
        ),
    ):
        result = await execute_atomic(mock_context, auto_generated_guid=SAMPLE_GUID)

    assert isinstance(result, ExecuteAtomicOutput)
    assert result.success is True
    assert result.atomic_name == "Test PowerShell"
    assert result.technique_id == "T1059.001"
    assert result.exit_code == 0


@pytest.mark.anyio
async def test_execute_atomic_error_in_result(mock_context):
    """Test that an error dict in the JSON result returns success=False."""
    run_output = json.dumps({"error": "Command not found"})

    with (
        patch(
            "atomic_red_team_mcp.tools.execute_atomic.load_atomics",
            return_value=[SAMPLE_ATOMIC],
        ),
        patch(
            "atomic_red_team_mcp.tools.execute_atomic.run_test",
            return_value=run_output,
        ),
    ):
        result = await execute_atomic(mock_context, auto_generated_guid=SAMPLE_GUID)

    assert isinstance(result, ExecuteAtomicOutput)
    assert result.success is False
    assert "Command not found" in result.error
