"""Tests for refresh_atomics tool."""

import uuid
from unittest.mock import Mock, patch

import pytest

from atomic_red_team_mcp.models import CommandExecutor, MetaAtomic, RefreshAtomicsOutput
from atomic_red_team_mcp.tools.refresh_atomics import refresh_atomics


@pytest.fixture
def mock_context():
    """Create a mock context with lifespan context."""
    ctx = Mock()
    ctx.request_context = Mock()
    ctx.request_context.lifespan_context = Mock()
    ctx.request_context.lifespan_context.atomics = []
    return ctx


@pytest.fixture
def sample_atomics():
    return [
        MetaAtomic(
            name="Test Atomic",
            description="Test",
            supported_platforms=["windows"],
            executor=CommandExecutor(name="powershell", command="Get-Process"),
            technique_id="T1059.001",
            auto_generated_guid=uuid.UUID("a8c41029-8d2a-4661-ab83-e5104c1cb667"),
        ),
    ]


@pytest.mark.anyio
async def test_refresh_atomics_success(mock_context, sample_atomics):
    """Test successful refresh updates context and returns correct output."""
    with (
        patch(
            "atomic_red_team_mcp.tools.refresh_atomics.download_atomics"
        ) as mock_download,
        patch(
            "atomic_red_team_mcp.tools.refresh_atomics.load_atomics",
            return_value=sample_atomics,
        ) as mock_load,
    ):
        result = await refresh_atomics(mock_context)

    mock_download.assert_called_once_with(force=True)
    mock_load.assert_called_once()

    assert isinstance(result, RefreshAtomicsOutput)
    assert result.success is True
    assert result.atomics_count == len(sample_atomics)
    assert mock_context.request_context.lifespan_context.atomics == sample_atomics


@pytest.mark.anyio
async def test_refresh_atomics_failure_returns_structured_output(mock_context):
    """Test that download failures return success=False instead of raising."""
    with patch(
        "atomic_red_team_mcp.tools.refresh_atomics.download_atomics",
        side_effect=Exception("Network error"),
    ):
        result = await refresh_atomics(mock_context)

    assert isinstance(result, RefreshAtomicsOutput)
    assert result.success is False
    assert result.atomics_count == 0
    assert "Network error" in result.message


@pytest.mark.anyio
async def test_refresh_atomics_load_failure_returns_structured_output(mock_context):
    """Test that load failures also return success=False."""
    with (
        patch("atomic_red_team_mcp.tools.refresh_atomics.download_atomics"),
        patch(
            "atomic_red_team_mcp.tools.refresh_atomics.load_atomics",
            side_effect=Exception("Parse error"),
        ),
    ):
        result = await refresh_atomics(mock_context)

    assert isinstance(result, RefreshAtomicsOutput)
    assert result.success is False
    assert "Parse error" in result.message
