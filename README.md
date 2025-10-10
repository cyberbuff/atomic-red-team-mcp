# Atomic Red Team MCP Server

An MCP (Model Context Protocol) server that provides access to Atomic Red Team tests.

## Available Tools and Resources

The server provides the following MCP tools:

- `query_atomics` - Search atomics by technique ID, name, description, or platform
- `refresh_atomics` - Download latest atomics from GitHub
- `validate_atomic` - Validate atomic test YAML
- `get_validation_schema` - Get the atomic test schema
- `execute_atomic` - Execute atomic tests (requires `ART_EXECUTION_ENABLED=true`)

And resources:
- `file://documents/{technique_id}` - Read atomic test files by technique ID

### Usage Examples

- "Search mshta atomics for windows"
- "Show me all the atomic tests for T1059.002"
- "Find all the applescript atomics for macOS"
- "Validate this atomic test YAML <yaml-content-here>"

## Installation

The Atomic Red Team MCP server can be installed in various development tools and AI assistants. Choose your platform below for detailed installation instructions:

### Quick Start

**Recommended: Using uvx**
```bash
uvx atomic-red-team-mcp
```

**Using Docker**
```bash
docker run --rm -i ghcr.io/cyberbuff/atomic-red-team-mcp:latest
```

### Platform-Specific Guides
- **[VSCode](https://github.com/cyberbuff/atomic-red-team-mcp/blob/main/guides/code.md)** - Installation guide for VSCode
- **[Claude Desktop & Claude Code](https://github.com/cyberbuff/atomic-red-team-mcp/blob/main/guides/claude.md)** - Installation guide for Anthropic's Claude Desktop app and Claude Code CLI
- **[Cursor](https://github.com/cyberbuff/atomic-red-team-mcp/blob/main/guides/cursor.md)** - Installation guide for Cursor IDE
- **[Windsurf](https://github.com/cyberbuff/atomic-red-team-mcp/blob/main/guides/windsurf.md)** - Installation guide for Windsurf editor
- **[Google AI Studio / Gemini](https://github.com/cyberbuff/atomic-red-team-mcp/blob/main/guides/gemini.md)** - Installation guide for Google's AI tools
- **[Other Tools](https://github.com/cyberbuff/atomic-red-team-mcp/blob/main/guides/other.md)** - Cline, Zed, and generic MCP clients

### Installation Methods

Each platform supports multiple installation methods:

1. **uvx (Recommended)** - Easiest setup, automatic updates
2. **Docker** - Isolated environment, consistent across systems
3. **Remote Server** ⚠️ - Hosted on Railway (free tier, may have limits)

## Configuration

### Environment Variables

#### Server Configuration
- `ART_MCP_TRANSPORT` - Transport protocol (stdio, sse, streamable-http)
- `ART_MCP_HOST` - Server host address (default: 0.0.0.0)
- `ART_MCP_PORT` - Server port number (default: 8000)

#### Repository Configuration
- `ART_GITHUB_URL` - GitHub URL for atomics repository (default: https://github.com)
- `ART_GITHUB_USER` - GitHub user/org (default: redcanaryco)
- `ART_GITHUB_REPO` - Repository name (default: atomic-red-team)
- `ART_DATA_DIR` - Local directory path where atomic test files are stored (default: ./atomics)

#### Security Configuration
- `ART_EXECUTION_ENABLED` - Enable the `execute_atomic` tool (default: false). Set to `true`, `1`, or `yes` to enable. **⚠️ WARNING: Only enable in controlled environments as this allows executing potentially dangerous security tests.**
- Enable Authentication if you are hosting a remote MCP server

#### Authentication Configuration
- `ART_AUTH_TOKEN` - Static bearer token for authentication (optional, authentication disabled if not set)
- `ART_AUTH_CLIENT_ID` - Client identifier for authenticated requests (default: authorized-client)

### Enabling Atomic Test Execution

By default, the `execute_atomic` tool is **disabled** for safety reasons. To enable it:

```bash
# Using uvx
ART_EXECUTION_ENABLED=true uvx atomic-red-team-mcp
```

**⚠️ Security Warning**: Only enable atomic test execution in controlled, isolated environments (like test VMs or sandboxes). These tests can modify system state, create files, execute commands, and perform actions that may be flagged as malicious by security tools.

### Authentication

The server supports static token authentication for securing access to the MCP tools and resources. When enabled, clients must include a bearer token in the `Authorization` header:

```
Authorization: Bearer <your-token>
```

**To enable authentication:**

1. Set the `ART_AUTH_TOKEN` environment variable:
   ```bash
   export ART_AUTH_TOKEN="your-secure-token-here"
   ```

2. Start the server (authentication is automatically enabled)

3. Clients authenticate by including the token in requests:
   ```bash
   curl -H "Authorization: Bearer your-secure-token-here" http://localhost:8000
   ```

**Security Notes:**
- Authentication is disabled by default (no token required)
- When `ART_AUTH_TOKEN` is set, all requests must include a valid bearer token
- Use strong, randomly generated tokens in production
- Never commit tokens to version control
- For development/testing, use a simple token. For production, use a cryptographically secure token

**Example with Docker:**
```bash
docker run --rm -i \
  -e ART_AUTH_TOKEN="my-secure-token" \
  -e ART_AUTH_CLIENT_ID="my-client" \
  ghcr.io/cyberbuff/atomic-red-team-mcp:latest
```
