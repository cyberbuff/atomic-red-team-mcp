"""Entry point for running the MCP server as a module."""

import logging
import os


from atomic_red_team_mcp.server import create_mcp_server

# Configure logging to stderr to avoid interfering with MCP JSON protocol
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Disable INFO messages from noisy loggers
logging.getLogger("mcp.server.lowlevel.server").setLevel(logging.ERROR)
logging.getLogger("mcp.server.streamable_http_manager").setLevel(logging.ERROR)
logging.getLogger("sse_starlette.sse").setLevel(logging.ERROR)


def main():
    """Main entry point for the CLI."""
    transport = os.getenv("ART_MCP_TRANSPORT", "stdio")
    mcp = create_mcp_server()
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
