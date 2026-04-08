"""Tests for query_atomics tool."""

import uuid
from unittest.mock import Mock

import pytest

from atomic_red_team_mcp.models import CommandExecutor, MetaAtomic, QueryAtomicsOutput
from atomic_red_team_mcp.services import create_index
from atomic_red_team_mcp.tools.query_atomics import query_atomics


@pytest.fixture
def mock_context():
    """Create a mock context with sample atomic tests."""
    ctx = Mock()

    atomics = [
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
    ctx.lifespan_context = {"atomics": atomics, "index": create_index(atomics)}

    return ctx


def test_query_basic(mock_context):
    """Test basic query functionality."""
    result = query_atomics(mock_context, query="powershell")

    assert isinstance(result, QueryAtomicsOutput)
    assert result.total_results >= 0
    assert len(result.atomics) <= result.total_results


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
    """Test cursor-based pagination works correctly."""
    page1 = query_atomics(mock_context, query="test", limit=1)

    assert len(page1.atomics) <= 1
    if page1.total_results > 1:
        assert page1.next_cursor is not None
        # Page 2 using cursor
        page2 = query_atomics(
            mock_context, query="test", limit=1, cursor=page1.next_cursor
        )
        assert len(page2.atomics) <= 1
    else:
        assert page1.next_cursor is None


def test_query_empty_query():
    """Test that empty query raises ValueError."""
    ctx = Mock()
    ctx.lifespan_context = {"atomics": [], "index": None}
    with pytest.raises(ValueError, match="Query parameter cannot be empty"):
        query_atomics(ctx, query="")


def test_query_invalid_technique_id():
    """Test that invalid technique ID format raises ValueError."""
    ctx = Mock()
    ctx.lifespan_context = {"atomics": [], "index": None}
    with pytest.raises(ValueError, match="Invalid technique ID format"):
        query_atomics(ctx, query="test", technique_id="T1234X")


def test_query_invalid_limit():
    """Test that invalid limit raises ValueError."""
    ctx = Mock()
    ctx.lifespan_context = {"atomics": [], "index": None}
    with pytest.raises(ValueError, match="limit must be between"):
        query_atomics(ctx, query="test", limit=201)


def test_query_invalid_cursor(mock_context):
    """Test that an invalid cursor raises ValueError."""
    with pytest.raises(ValueError, match="Invalid cursor"):
        query_atomics(mock_context, query="test", cursor="not-valid-base64!!")


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
