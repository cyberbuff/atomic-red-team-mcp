"""Tests for query_atomics tool."""

import uuid
from unittest.mock import Mock

import pytest

from atomic_red_team_mcp.models import CommandExecutor, MetaAtomic, QueryAtomicsOutput
from atomic_red_team_mcp.tools.query_atomics import query_atomics


@pytest.fixture
def mock_context():
    """Create a mock context with sample atomic tests."""
    ctx = Mock()
    ctx.request_context = Mock()
    ctx.request_context.lifespan_context = Mock()

    # Create sample atomic tests
    ctx.request_context.lifespan_context.atomics = [
        MetaAtomic(
            name="Test PowerShell Execution",
            description="Test PowerShell execution",
            supported_platforms=["windows"],
            executor=CommandExecutor(name="powershell", command="Get-Process"),
            technique_id="T1059.001",
            technique_name="PowerShell",
            auto_generated_guid=uuid.UUID("a8c41029-8d2a-4661-ab83-e5104c1cb667"),
        ),
        MetaAtomic(
            name="Test Bash Execution",
            description="Test bash execution",
            supported_platforms=["linux", "macos"],
            executor=CommandExecutor(name="bash", command="ls -la"),
            technique_id="T1059.004",
            technique_name="Unix Shell",
            auto_generated_guid=uuid.UUID("b9c41029-8d2a-4661-ab83-e5104c1cb668"),
        ),
    ]

    return ctx


def test_query_basic(mock_context):
    """Test basic query functionality."""
    result = query_atomics(mock_context, query="powershell")

    assert isinstance(result, QueryAtomicsOutput)
    assert result.total_results >= 0
    assert result.returned_count <= result.total_results
    assert len(result.atomics) == result.returned_count


def test_query_with_technique_id(mock_context):
    """Test query filtering by technique ID."""
    result = query_atomics(mock_context, query="", technique_id="T1059.001")

    assert result.total_results == 1
    assert result.atomics[0].technique_id == "T1059.001"


def test_query_with_platform(mock_context):
    """Test query filtering by platform."""
    result = query_atomics(mock_context, query="", supported_platforms="windows")

    assert result.total_results >= 0
    for atomic in result.atomics:
        assert "windows" in atomic.supported_platforms


def test_query_with_guid(mock_context):
    """Test query filtering by GUID."""
    result = query_atomics(
        mock_context, query="", guid="a8c41029-8d2a-4661-ab83-e5104c1cb667"
    )

    assert result.total_results == 1
    assert (
        str(result.atomics[0].auto_generated_guid)
        == "a8c41029-8d2a-4661-ab83-e5104c1cb667"
    )


def test_query_pagination(mock_context):
    """Test pagination works correctly."""
    # First page
    page1 = query_atomics(mock_context, query="test", limit=1, offset=0)

    assert page1.returned_count <= 1
    if page1.total_results > 1:
        assert page1.has_more
        assert page1.next_offset == 1
    else:
        assert not page1.has_more


def test_query_empty_query():
    """Test that empty query raises ValueError."""
    ctx = Mock()
    with pytest.raises(ValueError, match="Query parameter cannot be empty"):
        query_atomics(ctx, query="")


def test_query_invalid_technique_id():
    """Test that invalid technique ID format raises ValueError."""
    ctx = Mock()
    with pytest.raises(ValueError, match="Invalid technique ID format"):
        query_atomics(ctx, query="test", technique_id="T1234X")


def test_query_invalid_limit():
    """Test that invalid limit raises ValueError."""
    ctx = Mock()
    with pytest.raises(ValueError, match="Invalid limit"):
        query_atomics(ctx, query="test", limit=101)


def test_query_negative_offset():
    """Test that negative offset raises ValueError."""
    ctx = Mock()
    with pytest.raises(ValueError, match="Invalid offset"):
        query_atomics(ctx, query="test", offset=-1)


def test_query_metadata(mock_context):
    """Test that query metadata is populated correctly."""
    result = query_atomics(
        mock_context,
        query="test",
        technique_id="T1059.001",
        supported_platforms="windows",
    )

    assert "query" in result.query_metadata
    assert result.query_metadata["query"] == "test"
    assert "filters_applied" in result.query_metadata
    assert len(result.query_metadata["filters_applied"]) > 0
