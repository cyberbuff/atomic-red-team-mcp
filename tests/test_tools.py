"""In-memory MCP client tests using FastMCP's Client transport."""

from unittest.mock import patch

import pytest
from fastmcp import Client

from atomic_red_team_mcp.models import MetaAtomic
from atomic_red_team_mcp.server.app import create_mcp_server

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

WINDOWS_ATOMIC = MetaAtomic(
    name="PowerShell Process Enumeration",
    description="Lists running processes using PowerShell",
    supported_platforms=["windows"],
    executor={"name": "powershell", "command": "Get-Process"},
    technique_id="T1059.001",
    technique_name="PowerShell",
)

LINUX_ATOMIC = MetaAtomic(
    name="Bash Directory Listing",
    description="Lists directory contents using bash",
    supported_platforms=["linux"],
    executor={"name": "bash", "command": "ls /tmp"},
    technique_id="T1059.004",
    technique_name="Unix Shell",
)

TEST_ATOMICS = [WINDOWS_ATOMIC, LINUX_ATOMIC]


@pytest.fixture
def mcp_server():
    """MCP server with atomics loading mocked out."""
    from atomic_red_team_mcp.services import create_index

    with (
        patch("atomic_red_team_mcp.server.app.download_atomics"),
        patch("atomic_red_team_mcp.server.app.load_atomics", return_value=TEST_ATOMICS),
        patch(
            "atomic_red_team_mcp.server.app.create_index",
            return_value=create_index(TEST_ATOMICS),
        ),
    ):
        yield create_mcp_server()


# ---------------------------------------------------------------------------
# server_info
# ---------------------------------------------------------------------------


async def test_server_info(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("server_info", {})
        info = result.data
        assert info.name == "Atomic Red Team MCP"
        assert info.version
        assert info.os
        assert info.transport
        assert info.data_directory


# ---------------------------------------------------------------------------
# query_atomics
# ---------------------------------------------------------------------------


async def test_query_atomics_full_text_match(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("query_atomics", {"query": "directory listing"})
        data = result.data
        assert data.total_results == 1
        assert data.next_cursor is None
        assert data.atomics[0].name == "Bash Directory Listing"


async def test_query_atomics_filters_by_platform(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "query_atomics", {"query": "listing", "supported_platforms": "windows"}
        )
        data = result.data
        assert data.total_results == 0
        assert data.atomics == []
        assert data.next_cursor is None


async def test_query_atomics_filters_by_technique_id(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "query_atomics", {"query": "Process", "technique_id": "T1059.001"}
        )
        data = result.data
        assert data.total_results == 1
        assert data.atomics[0].technique_id == "T1059.001"


async def test_query_atomics_rejects_invalid_technique_id(mcp_server):
    async with Client(mcp_server) as client:
        with pytest.raises(Exception):
            await client.call_tool(
                "query_atomics", {"query": "test", "technique_id": "INVALID"}
            )


async def test_query_atomics_rejects_empty_query(mcp_server):
    async with Client(mcp_server) as client:
        with pytest.raises(Exception):
            await client.call_tool("query_atomics", {"query": ""})


async def test_query_atomics_pagination(mcp_server):
    async with Client(mcp_server) as client:
        # Both atomics match "technique" via their fields
        r1 = await client.call_tool("query_atomics", {"query": "technique", "limit": 1})
        d1 = r1.data
        assert d1.total_results == 2
        assert len(d1.atomics) == 1
        assert d1.next_cursor is not None

        # Page 2: use cursor from page 1
        r2 = await client.call_tool(
            "query_atomics",
            {"query": "technique", "limit": 1, "cursor": d1.next_cursor},
        )
        d2 = r2.data
        assert d2.total_results == 2
        assert len(d2.atomics) == 1
        assert d2.next_cursor is None
        assert d1.atomics[0].name != d2.atomics[0].name


async def test_query_atomics_rejects_invalid_limit(mcp_server):
    async with Client(mcp_server) as client:
        with pytest.raises(Exception):
            await client.call_tool("query_atomics", {"query": "test", "limit": 0})


async def test_query_atomics_rejects_invalid_cursor(mcp_server):
    async with Client(mcp_server) as client:
        with pytest.raises(Exception):
            await client.call_tool(
                "query_atomics", {"query": "test", "cursor": "not-valid-base64!!"}
            )


# ---------------------------------------------------------------------------
# get_validation_schema
# ---------------------------------------------------------------------------


async def test_get_validation_schema(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("get_validation_schema", {})
        schema = result.data
        assert "properties" in schema
        assert "required" in schema
        assert "name" in schema["properties"]
        assert "executor" in schema["properties"]
        assert "supported_platforms" in schema["properties"]


# ---------------------------------------------------------------------------
# validate_atomic
# ---------------------------------------------------------------------------

_VALID_YAML = """
name: Test PowerShell Process Listing
description: Lists running processes using PowerShell for testing
supported_platforms:
  - windows
executor:
  name: powershell
  command: Get-Process
"""

_INVALID_YAML = """
name: Incomplete Test
description: Missing required executor field
supported_platforms:
  - linux
"""

_GUID_WARNING_YAML = """
name: Test With GUID Warning
description: Atomic test that includes auto_generated_guid triggering a warning
supported_platforms:
  - linux
executor:
  name: bash
  command: ls /tmp
auto_generated_guid: 12345678-1234-1234-1234-123456789012
"""


async def test_validate_atomic_valid(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("validate_atomic", {"yaml_string": _VALID_YAML})
        assert result.data.valid is True
        assert result.data.warnings is None


async def test_validate_atomic_invalid(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "validate_atomic", {"yaml_string": _INVALID_YAML}
        )
        assert result.data.valid is False
        assert result.data.error is not None


async def test_validate_atomic_warns_on_guid(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "validate_atomic", {"yaml_string": _GUID_WARNING_YAML}
        )
        assert result.data.valid is True
        assert result.data.warnings is not None
        assert any("auto_generated_guid" in w for w in result.data.warnings)


async def test_validate_atomic_rejects_empty_input(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("validate_atomic", {"yaml_string": ""})
        assert result.data.valid is False


# ---------------------------------------------------------------------------
# refresh_atomics
# ---------------------------------------------------------------------------


async def test_refresh_atomics(mcp_server):
    with (
        patch("atomic_red_team_mcp.tools.refresh_atomics.download_atomics"),
        patch(
            "atomic_red_team_mcp.tools.refresh_atomics.load_atomics",
            return_value=TEST_ATOMICS,
        ),
    ):
        async with Client(mcp_server) as client:
            result = await client.call_tool("refresh_atomics", {})
            assert result.data.success is True
            assert result.data.atomics_count == 2


# ---------------------------------------------------------------------------
# tool tags
# ---------------------------------------------------------------------------


async def test_tool_tags(mcp_server):
    async with Client(mcp_server) as client:
        tools = await client.list_tools()
        tool_map = {t.name: t for t in tools}

        def tags(tool_name: str) -> set[str]:
            return set(tool_map[tool_name].meta["fastmcp"]["tags"])

        assert tags("server_info") == {"admin"}
        assert tags("refresh_atomics") == {"admin"}
        assert tags("query_atomics") == {"query", "search"}
        assert tags("get_validation_schema") == {"validation"}
        assert tags("validate_atomic") == {"validation"}
        assert tags("generate_atomic") == {"creation"}
