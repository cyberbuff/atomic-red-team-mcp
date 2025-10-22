# Installing Atomic Red Team MCP Server in Gemini CLI

This guide will help you install and configure the Atomic Red Team MCP server for use with the Gemini CLI.

## Prerequisites

- Node.js version 18 or higher installed ([download here](https://nodejs.org/))
- [Gemini CLI](https://github.com/google-gemini/gemini-cli) installed on your system
- Either:
  - [uv](https://docs.astral.sh/uv/) installed (recommended), or
  - [Docker](https://www.docker.com/) installed, or
  - Access to the remote server

## Installing Gemini CLI

If you haven't installed Gemini CLI yet:

```bash
# Install globally
npm install -g @google/gemini-cli

# Or run directly with npx
npx @google/gemini-cli
```

To launch and authenticate:

```bash
gemini
```

Follow the on-screen instructions to sign in with your Google account.

## MCP Server Installation Options

### Option 1: Using uvx (Recommended)

This is the easiest and recommended method for most users.

1. **Locate your Gemini CLI configuration file:**

   - **Global configuration**: `~/.gemini/settings.json` (where `~` is your home directory)
   - **Project-specific**: `.gemini/settings.json` in your project directory

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

3. **Restart the Gemini CLI**

The server will automatically download and run when you start the Gemini CLI.

### Option 2: Using Docker

If you prefer to use Docker:

1. **Pull the Docker image (optional, it will auto-pull if not present):**

```bash
docker pull ghcr.io/cyberbuff/atomic-red-team-mcp:latest
```

2. **Add the following configuration to your Gemini CLI MCP config:**

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

3. **Restart the Gemini CLI**

### ⚠️ Option 3: Remote Server

⚠️ **Warning**: The MCP server is running on a free instance of [Railway](https://railway.com/). It may go offline after the usage limits are reached.

1. **Add the following configuration:**

```json
{
	"mcpServers": {
		"atomic-red-team": {
			"url": "https://atomic-red-team-mcp.up.railway.app/mcp"
		}
	}
}
```

2. **Restart the Gemini CLI**
