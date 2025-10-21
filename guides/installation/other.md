# Installing Atomic Red Team MCP Server in Other Tools

This guide covers installation for various other tools and clients that support MCP.

## Table of Contents

- [Cline (VS Code Extension)](#cline-vs-code-extension)
- [Zed Editor](#zed-editor)
- [Generic MCP Client](#generic-mcp-client)

______________________________________________________________________

## Cline (VS Code Extension)

[Cline](https://github.com/cline/cline) is a VS Code extension that supports MCP.

### Prerequisites

- VS Code installed
- Cline extension installed
- Either uv or Docker installed

### Using uvx (Recommended)

Add to your Cline extension settings or `.cline_mcp_config.json`:

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

### Using Docker

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

### ⚠️ Remote Server

⚠️ **Warning**: The remote server runs on a free Railway instance and may go offline.

```json
{
 "mcpServers": {
  "atomic-red-team": {
   "url": "https://atomic-red-team-mcp.up.railway.app/mcp"
  }
 }
}
```

______________________________________________________________________

## Zed Editor

[Zed](https://zed.dev/) is a modern code editor with MCP support.

### Prerequisites

- Zed Editor installed
- Either uv or Docker installed

### Using uvx (Recommended)

Add to your Zed settings (`settings.json`):

```json
{
 "experimental": {
  "mcp": {
   "servers": {
    "atomic-red-team": {
     "command": "uvx",
     "args": ["atomic-red-team-mcp"]
    }
   }
  }
 }
}
```

### Using Docker

```json
{
 "experimental": {
  "mcp": {
   "servers": {
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
 }
}
```

### ⚠️ Remote Server

⚠️ **Warning**: The remote server runs on a free Railway instance and may go offline.

```json
{
 "experimental": {
  "mcp": {
   "servers": {
    "atomic-red-team": {
     "url": "https://atomic-red-team-mcp.up.railway.app/mcp"
    }
   }
  }
 }
}
```

______________________________________________________________________

## Generic MCP Client

For any MCP client that supports stdio transport:

### Using uvx (Recommended)

```bash
uvx atomic-red-team-mcp
```

### Using Docker

```bash
docker run --rm -i ghcr.io/cyberbuff/atomic-red-team-mcp:latest
```

### ⚠️ Remote Server

⚠️ **Warning**: The remote server runs on a free Railway instance and may go offline.

```bash
# Use this URL in your MCP client configuration
https://atomic-red-team-mcp.up.railway.app/mcp
```
