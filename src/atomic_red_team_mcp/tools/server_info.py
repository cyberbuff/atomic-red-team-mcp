"""Server information tool."""

import platform
from importlib.metadata import PackageNotFoundError, version

from fastmcp import Context

from atomic_red_team_mcp.utils.config import get_settings

# Get version from package metadata
try:
    __version__ = version("atomic-red-team-mcp")
except PackageNotFoundError:
    __version__ = "dev"


def server_info(ctx: Context) -> dict:
    """Get comprehensive information about the MCP server configuration and environment.

    This tool returns server metadata including version, transport protocol, operating system,
    and data directory location. Use this to:
    - Verify server configuration
    - Check server version for compatibility
    - Confirm the platform before executing atomic tests
    - Locate the atomic tests data directory

    Args:
        ctx: MCP context (provided automatically by the framework)

    Returns:
        dict: Server information with the following fields:
            - name (str): Server name - always "Atomic Red Team MCP"
            - version (str): Installed package version (e.g., "1.2.3")
                           Shows "dev" if running from source without installation
            - transport (str): MCP transport protocol being used
                             Values: "stdio" (default), "sse", or "streamable-http"
            - os (str): Operating system platform
                       Values: "Darwin" (macOS), "Linux", "Windows"
                       Use this to verify test compatibility before execution
            - data_directory (str): Absolute path to atomic tests storage directory
                                   This is where atomic YAML files are stored
                                   Use this path when creating new atomic tests

    Examples:
        # Get server information
        info = server_info(ctx)
        print(f"Running version {info['version']} on {info['os']}")

        # Check if remote server for execution
        if info['transport'] == 'streamable-http':
            print("This is a remote MCP server")

        # Get data directory for creating tests
        data_dir = info['data_directory']
        print(f"Create new tests in: {data_dir}/T####/T####.yaml")

    Use Cases:
        1. **Before executing tests**: Check OS matches supported_platforms
        2. **Creating atomic tests**: Use data_directory to know where to save files
        3. **Debugging**: Verify configuration settings
        4. **Version compatibility**: Ensure tools match server version

    Notes:
        - This tool always succeeds and never raises exceptions
        - Information reflects the current runtime configuration
        - Transport and data_directory come from Settings (environment variables/.env)
        - OS is detected at runtime and cannot be changed
    """
    settings = get_settings()
    return {
        "name": "Atomic Red Team MCP",
        "version": __version__,
        "transport": settings.mcp_transport,
        "os": platform.system(),
        "data_directory": settings.get_atomics_dir(),
    }
