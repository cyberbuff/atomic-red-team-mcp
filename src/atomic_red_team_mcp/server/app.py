"""Main MCP server application."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import List

from fastmcp import Context, FastMCP
from starlette.responses import JSONResponse

from atomic_red_team_mcp.models import MetaAtomic
from atomic_red_team_mcp.server.auth import configure_auth
from atomic_red_team_mcp.server.resources import read_atomic_document
from atomic_red_team_mcp.services import download_atomics, load_atomics
from atomic_red_team_mcp.tools import (
    execute_atomic,
    get_validation_schema,
    query_atomics,
    refresh_atomics,
    server_info,
    validate_atomic,
)
from atomic_red_team_mcp.utils.config import get_atomics_dir

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    atomics: List[MetaAtomic]


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context."""
    # Download atomics on startup
    try:
        download_atomics()
        atomics = load_atomics()

        # Log execution tool status
        execution_enabled = os.getenv("ART_EXECUTION_ENABLED", "false").lower() in [
            "true",
            "1",
            "yes",
        ]
        if execution_enabled:
            logger.warning(
                "⚠️  Atomic test execution is ENABLED - tests can be executed on this system"
            )
        else:
            logger.info(
                "Atomic test execution is disabled. Set ART_EXECUTION_ENABLED=true to enable."
            )

        yield AppContext(atomics=atomics)
    finally:
        pass


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server."""
    is_http = os.getenv("ART_MCP_TRANSPORT", "stdio") == "streamable-http"
    is_execution_enabled = os.getenv("ART_EXECUTION_ENABLED", "false").lower() in [
        "true",
        "1",
        "yes",
    ]

    # Configure authentication
    auth = configure_auth()

    instructions = """
Use this MCP server to access and create Atomic Red Team tests for security testing.

AVAILABLE TOOLS:
- `query_atomics`: Search existing atomic tests by technique ID, name, description, or platform
- `refresh_atomics`: Update atomic tests from GitHub repository
- `get_validation_schema`: Get the JSON schema for atomic test structure
- `validate_atomic`: Validate atomic test YAML against the schema
- `server_info`: Get server information including version, transport, and OS platform
"""

    if is_execution_enabled:
        instructions += """
- `execute_atomic`: Execute an atomic test by GUID (requires ENABLE_ATOMIC_EXECUTION=true)
"""

    instructions += """
CREATING NEW ATOMIC TESTS:
When creating atomic tests, you are acting as an Offensive Security expert. Follow these best practices:

🎯 CORE REQUIREMENTS:
- Design tests that mirror actual adversary behavior and real-world attack patterns
- Always validate tests using `validate_atomic` tool before finalizing
- Use `get_validation_schema` first to understand the required structure
- Keep external dependencies to a minimum for better portability and reliability

🧹 SYSTEM SAFETY:
- Always include cleanup commands to restore the system to its original state if needed
- Ensure tests are fully functional and can be executed without errors
- Search online if needed to find manpages/documentation for tools used

📝 DOCUMENTATION STANDARDS:
- Use clear, descriptive names that indicate the technique being tested
- Provide comprehensive descriptions explaining what the test does and why
- Include external references if you used any online resources
- Clearly document any required tools, permissions, or system configurations
- If there are no prerequisites, omit the dependencies section

⚙️ IMPLEMENTATION BEST PRACTICES:
- Use parameterized inputs (input_arguments) for flexibility and reusability
- If there are no input arguments, omit the input_arguments section
- Do NOT use hardcoded values in commands - use input_arguments instead
- Do NOT include echo commands or print statements in the test commands
- Set elevation_required: true if using sudo or admin privileges
- Keep tests concise and focused on the specific technique being tested
- Do not create unnecessary files for saving output unless required for the test
- Do not add auto_generated_guid to the atomic test for new tests

WORKFLOW FOR CREATING ATOMIC TESTS:
1. Call `get_validation_schema` to understand the atomic test structure
2. Create the atomic test following the schema and best practices above
3. Call `validate_atomic` tool with the generated YAML to ensure it's valid
4. If validation fails, fix the issues and validate again until successful
5. Use `server_info` to get the data directory path and create the atomic test in the correct directory.
6. When creating a new atomic test, create them in the `<data_directory>/<technique_id>/<technique_id>.yaml` file.
7. If you have any dependencies for the atomic test, create them in the `<data_directory>/<technique_id>/src` folder.
"""

    if is_http and is_execution_enabled:
        instructions += """
🚀 ATOMIC TEST EXECUTION:
- This is a remote MCP server with atomic test execution enabled
- Execute atomic tests using the `execute_atomic` tool
- You will be prompted for input arguments if needed
- Use `server_info` to get the remote MCP server platform information
- The `supported_platforms` field should reflect the remote server platform, not the host platform
- There may be numerous Atomic Red Team MCP servers running on different platforms, so you need to check the platform of the remote MCP server before executing the atomic test.
"""

    mcp = FastMCP(
        "Atomic Red Team MCP",
        instructions=instructions,
        lifespan=app_lifespan,
        host=os.getenv("ART_MCP_HOST", "0.0.0.0"),
        port=int(os.getenv("ART_MCP_PORT", "8000")),
        auth=auth,
    )

    # Register resource
    @mcp.resource("file://documents/{technique_id}")
    def read_document(technique_id: str, ctx: Context) -> str:
        """Read a atomic test file by technique ID."""
        atomics_dir = get_atomics_dir()
        return read_atomic_document(technique_id, atomics_dir)

    # Register tools
    mcp.tool()(server_info)
    mcp.tool()(refresh_atomics)
    mcp.tool()(query_atomics)
    mcp.tool()(get_validation_schema)
    mcp.tool()(validate_atomic)
    mcp.tool(enabled=is_execution_enabled)(execute_atomic)

    # Register custom routes
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request):
        return JSONResponse({"status": "healthy", "service": "atomic-red-team-mcp"})

    return mcp
