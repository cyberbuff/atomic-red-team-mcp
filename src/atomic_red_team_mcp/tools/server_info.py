"""Server information tool."""

import os
import platform
from importlib.metadata import PackageNotFoundError, version

from fastmcp import Context

from atomic_red_team_mcp.utils.config import get_atomics_dir

# Get version from package metadata
try:
    __version__ = version("atomic-red-team-mcp")
except PackageNotFoundError:
    __version__ = "dev"


def server_info(ctx: Context) -> dict:
    """Get server information."""
    return {
        "name": "Atomic Red Team MCP",
        "version": __version__,
        "transport": os.getenv("ART_MCP_TRANSPORT", "stdio"),
        "os": platform.system(),
        "data_directory": get_atomics_dir(),
    }
