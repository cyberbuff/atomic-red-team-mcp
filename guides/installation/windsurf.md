# Installing Atomic Red Team MCP Server in Windsurf

This guide will help you install and configure the Atomic Red Team MCP server for use with Windsurf.

## Prerequisites

- [Windsurf](https://codeium.com/windsurf) installed on your system
- Either:
  - [uv](https://docs.astral.sh/uv/) installed (recommended), or
  - [Docker](https://www.docker.com/) installed, or
  - Access to the remote server

## Installation

1.  **Open Windsurf Settings** by pressing `Cmd+,` (macOS) or `Ctrl+,` (Windows/Linux), or by directly editing your MCP configuration file.
2.  **Add the server configuration** using one of the options below.
3.  **Restart Windsurf** to apply the changes.

### Option 1: Using uvx (Recommended)


```json
{
  "mcpServers": {
    "atomic-red-team": {
      "command": "uvx",
      "args": ["atomic-red-team-mcp"]
    }
  }
}
```

### Option 2: Using Docker

If you prefer to use Docker, you can optionally pull the image beforehand:

```bash
docker pull ghcr.io/cyberbuff/atomic-red-team-mcp:latest
```

Then, add this configuration:

```json
{
  "mcpServers": {
    "atomic-red-team": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "ghcr.io/cyberbuff/atomic-red-team-mcp:latest"
      ]
    }
  }
}
```

### ⚠️ Option 3: Remote Server

⚠️ **Warning**: The MCP server is running on a free instance of [Railway](https://railway.com/) and may go offline if usage limits are reached.

```json
{
  "mcpServers": {
    "atomic-red-team": {
      "url": "https://atomic-red-team-mcp.up.railway.app/mcp"
    }
  }
}
```
