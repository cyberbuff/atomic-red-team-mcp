# Installing Atomic Red Team MCP Server in Cursor

This guide will help you install and configure the Atomic Red Team MCP server for use with Cursor.

## Prerequisites

- [Cursor](https://cursor.com/) installed on your system
- Either:
  - [uv](https://docs.astral.sh/uv/) installed (recommended), or
  - [Docker](https://www.docker.com/) installed, or
  - Access to the remote server

## Installation Options

### Option 1: Using uvx (Recommended)

This is the easiest and recommended method for most users.

1. **Open Cursor Settings:**

   - Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
   - Type "Preferences: Open User Settings (JSON)"
   - Or directly edit your MCP config file at `~/.cursor/mcp.json`

1. **Add the following configuration:**

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

**With Execution Enabled:**

To enable atomic test execution (⚠️ **Warning**: This allows the MCP server to execute security tests on your system):

```json
{
	"mcpServers": {
		"atomic-red-team": {
			"command": "uvx",
			"args": ["atomic-red-team-mcp"],
			"env": {
				"ART_EXECUTION_ENABLED": "true"
			}
		}
	}
}
```

3. **Restart Cursor**

The server will automatically download and run when Cursor starts.

### Option 2: Using Docker

If you prefer to use Docker:

1. **Pull the Docker image (optional, it will auto-pull if not present):**

```bash
docker pull ghcr.io/cyberbuff/atomic-red-team-mcp:latest
```

2. **Add the following configuration to your Cursor settings:**

```json
{
	"mcpServers": {
		"atomic-red-team": {
			"command": "docker",
			"args": [
				"run",
				"--rm",
				"-i",
				"ghcr.io/cyberbuff/atomic-red-team-mcp:latest"
			]
		}
	}
}
```

**With Execution Enabled:**

To enable atomic test execution (⚠️ **Warning**: This allows the MCP server to execute security tests on your system):

```json
{
	"mcpServers": {
		"atomic-red-team": {
			"command": "docker",
			"args": [
				"run",
				"--rm",
				"-i",
				"-e",
				"ART_EXECUTION_ENABLED=true",
				"ghcr.io/cyberbuff/atomic-red-team-mcp:latest"
			]
		}
	}
}
```

3. **Restart Cursor**

### ⚠️ Option 3: Remote Server

⚠️ **Warning**: The MCP server is running on a free instance of [Railway](https://railway.com/). It may go offline after the usage limits are reached.

1. **Add the following configuration to your Cursor settings:**

```json
{
	"mcpServers": {
		"atomic-red-team": {
			"url": "https://atomic-red-team-mcp.up.railway.app/mcp"
		}
	}
}
```

2. **Restart Cursor**
