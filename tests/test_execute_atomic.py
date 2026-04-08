"""Tests for execute_atomic tool."""

import uuid
from unittest.mock import AsyncMock, MagicMock, Mock, patch

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
    ctx.report_progress = AsyncMock()
    return ctx


def _make_runner(captured_outputs):
    """Build a mock AtomicRunner context manager with given captured_outputs."""
    runner = MagicMock()
    runner.captured_outputs = captured_outputs
    runner.run_phase = Mock()
    runner.__enter__ = Mock(return_value=runner)
    runner.__exit__ = Mock(return_value=False)
    return runner


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
async def test_execute_atomic_runner_exception(mock_context):
    """Test that an AtomicRunner exception returns success=False with error detail."""
    runner = _make_runner([])
    runner.__enter__ = Mock(side_effect=RuntimeError("runner blew up"))

    with (
        patch(
            "atomic_red_team_mcp.tools.execute_atomic.load_atomics",
            return_value=[SAMPLE_ATOMIC],
        ),
        patch(
            "atomic_red_team_mcp.tools.execute_atomic.AtomicRunner",
            return_value=runner,
        ),
    ):
        result = await execute_atomic(mock_context, auto_generated_guid=SAMPLE_GUID)

    assert isinstance(result, ExecuteAtomicOutput)
    assert result.success is False
    assert "runner blew up" in result.error


@pytest.mark.anyio
async def test_execute_atomic_success(mock_context):
    """Test successful execution returns structured output with correct fields."""
    captured = [
        {"phase": "test", "output": "stdout text", "errors": "", "return_code": 0}
    ]
    runner = _make_runner(captured)

    with (
        patch(
            "atomic_red_team_mcp.tools.execute_atomic.load_atomics",
            return_value=[SAMPLE_ATOMIC],
        ),
        patch(
            "atomic_red_team_mcp.tools.execute_atomic.AtomicRunner",
            return_value=runner,
        ),
    ):
        result = await execute_atomic(mock_context, auto_generated_guid=SAMPLE_GUID)

    assert isinstance(result, ExecuteAtomicOutput)
    assert result.success is True
    assert result.atomic_name == "Test PowerShell"
    assert result.technique_id == "T1059.001"
    assert result.exit_code == 0


@pytest.mark.anyio
async def test_execute_atomic_nonzero_exit(mock_context):
    """Test that a non-zero exit code from a phase returns success=False."""
    captured = [
        {"phase": "execution", "output": "", "errors": "fail", "return_code": 1}
    ]
    runner = _make_runner(captured)

    with (
        patch(
            "atomic_red_team_mcp.tools.execute_atomic.load_atomics",
            return_value=[SAMPLE_ATOMIC],
        ),
        patch(
            "atomic_red_team_mcp.tools.execute_atomic.AtomicRunner",
            return_value=runner,
        ),
    ):
        result = await execute_atomic(mock_context, auto_generated_guid=SAMPLE_GUID)

    assert isinstance(result, ExecuteAtomicOutput)
    assert result.success is False
    assert result.exit_code == 1
