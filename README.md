# Atomic Red Team MCP Server

An MCP (Model Context Protocol) server that provides access to Atomic Red Team tests.

## Available Tools and Resources

The server provides the following MCP tools:

- `query_atomics` - Search atomics by technique ID, name, description, or platform
- `refresh_atomics` - Download latest atomics from GitHub
- `validate_atomic` - Validate atomic test YAML
- `get_validation_schema` - Get the atomic test schema

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

Environment variables:
- `MCP_TRANSPORT` - Transport protocol (stdio, sse, streamable-http)
- `MCP_HOST` - Host address to bind the server (default: 0.0.0.0)
- `MCP_PORT` - Port for HTTP transports (default: 8000)
- `GITHUB_URL` - GitHub URL for atomics repository (default: https://github.com)
- `GITHUB_USER` - GitHub user/org (default: redcanaryco)
- `GITHUB_REPO` - Repository name (default: atomic-red-team)
