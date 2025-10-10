# Installing Atomic Red Team MCP Server in Claude Desktop & Claude Code

This guide will help you install and configure the Atomic Red Team MCP server for use with Claude Desktop and Claude Code.

## Prerequisites

- **Claude Desktop** application or **Claude Code** CLI installed
- Either:
    - [uv](https://docs.astral.sh/uv/) installed (recommended), or
    - [Docker](https://www.docker.com/) installed, or
    - Access to the remote server

---

## Claude Desktop Installation

Claude Desktop requires manual configuration file editing.

### Installation Steps

1. **Locate your Claude Desktop configuration file:**
    - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
    - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
    - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. **Add the following configuration:**

**Using uvx:**

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

**Using Docker:**

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
				"ART_MCP_TRANSPORT",
				"ghcr.io/cyberbuff/atomic-red-team-mcp:latest"
			],
			"env": {
				"ART_MCP_TRANSPORT": "stdio"
			}
		}
	}
}
```

**Using Remote Server:**

⚠️ **Warning**: The MCP server is running on a free instance of [Railway](https://railway.com/). It may go offline after the usage limits are reached.

```json
{
	"mcpServers": {
		"atomic-red-team": {
			"url": "https://atomic-red-team-mcp.up.railway.app/mcp"
		}
	}
}
```

3. **Save the file and restart Claude Desktop**

---

## Claude Code Installation

Claude Code is a CLI tool that makes it easy to configure MCP servers.

### Using the CLI

The easiest way to add the Atomic Red Team MCP server to Claude Code:

#### Option 1: Using uvx (Recommended)

Open your terminal and run:

```bash
claude mcp add atomic-red-team uvx atomic-red-team-mcp
```

This command will automatically configure Claude Code to use the Atomic Red Team MCP server.

> **Note**: This requires [uv](https://docs.astral.sh/uv/) to be installed. If you don't have it:
>
> ```bash
> # macOS/Linux
> curl -LsSf https://astral.sh/uv/install.sh | sh
>
> # Windows
> powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
> ```

#### Option 2: Using Docker

```bash
claude mcp add atomic-red-team -- docker run --rm -i ghcr.io/cyberbuff/atomic-red-team-mcp:latest
```

#### Option 3: Using Remote Server ⚠️

⚠️ **Warning**: The MCP server is running on a free instance of [Railway](https://railway.com/). It may go offline after the usage limits are reached.

```bash
claude mcp add --transport http atomic-red-team https://atomic-red-team-mcp.up.railway.app/mcp
```
