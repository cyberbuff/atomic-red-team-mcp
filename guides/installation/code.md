# Installing Atomic Red Team MCP Server in VS Code

This guide will help you install and configure the Atomic Red Team MCP server for use with VS Code.

## Prerequisites

- [VS Code](https://code.visualstudio.com/) installed on your system
- Either:
  - [uv](https://docs.astral.sh/uv/) installed (recommended), or
  - [Docker](https://www.docker.com/) installed, or
  - Access to the remote server

## Installation Options

### Option 1: Using uvx (Recommended)

This is the easiest and recommended method for most users.

1. **Open VS Code Settings:**
   - Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
   - Type "Preferences: Open User Settings (JSON)"
   - Or directly edit your MCP config file at:
     - macOS/Linux: `~/.vscode/mcp.json`
     - Windows: `%APPDATA%\Code\User\mcp.json`

2. **Add the following configuration:**

```json
{
	"servers": {
		"atomic-red-team-mcp": {
			"command": "uvx",
			"args": ["atomic-red-team-mcp"]
		}
	}
}
```

3. **Restart VS Code**

The server will automatically download and run when VS Code starts.

### Option 2: Using Docker

If you prefer to use Docker:

1. **Pull the Docker image (optional, it will auto-pull if not present):**

```bash
docker pull ghcr.io/cyberbuff/atomic-red-team-mcp:latest
```

2. **Add the following configuration to your VS Code settings:**

```json
{
	"servers": {
		"atomic-red-team-mcp": {
			"command": "docker",
			"args": [
				"run", "--rm", "-i",
				"ghcr.io/cyberbuff/atomic-red-team-mcp:latest"
			]
		}
	}
}
```

3. **Restart VS Code**

### ⚠️ Option 3: Remote Server

⚠️ **Warning**: The MCP server is running on a free instance of [Railway](https://railway.com/). It may go offline after the usage limits are reached.

1. **Add the following configuration to your VS Code settings:**

```json
{
	"servers": {
		"atomic-red-team-mcp": {
			"url": "https://atomic-red-team-mcp.up.railway.app/mcp"
		}
	}
}
```

2. **Restart VS Code**
