# Architecture

This document describes the architecture and organization of the Atomic Red Team MCP Server.

## Project Structure

```
atomic-red-team-mcp/
├── src/                      # Main source code
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # CLI entry point
│   ├── models/              # Pydantic data models
│   │   ├── __init__.py
│   │   └── atomic.py        # Atomic test models
│   ├── server/              # MCP server logic
│   │   ├── __init__.py
│   │   ├── app.py          # Main server application
│   │   ├── auth.py         # Authentication configuration
│   │   └── resources.py    # MCP resource handlers
│   ├── services/            # Business logic layer
│   │   ├── __init__.py
│   │   ├── atomic_loader.py # Load/download atomics
│   │   └── executor.py     # Execute atomic tests
│   ├── tools/               # MCP tool implementations
│   │   ├── __init__.py
│   │   ├── execute_atomic.py
│   │   ├── query_atomics.py
│   │   ├── refresh_atomics.py
│   │   ├── server_info.py
│   │   └── validate_atomic.py
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── config.py        # Configuration helpers
├── tests/                   # Test suite
│   ├── __init__.py
│   └── test_imports.py
├── docs/                    # Documentation
│   └── ARCHITECTURE.md
├── atomics/                 # Atomic test data (downloaded)
├── guides/                  # Installation guides
├── .github/                 # GitHub workflows
├── pyproject.toml          # Project configuration
├── Dockerfile              # Docker image
└── README.md               # Project README

```

## Module Responsibilities

### `src/models/`

Contains Pydantic models for validating and serializing atomic test data:

- `Atomic`: Individual atomic test definition
- `MetaAtomic`: Atomic with metadata (technique ID, name)
- `Technique`: MITRE ATT&CK technique with atomic tests
- Type definitions and validators

### `src/server/`

MCP server implementation:

- `app.py`: Creates and configures the FastMCP server
- `auth.py`: Authentication configuration
- `resources.py`: MCP resource handlers (file reading)

### `src/services/`

Business logic layer:

- `atomic_loader.py`: Download and load atomic tests from GitHub
- `executor.py`: Execute atomic tests using atomic-operator

### `src/tools/`

Individual MCP tool implementations (one file per tool):

- `server_info.py`: Get server information
- `query_atomics.py`: Search atomic tests
- `refresh_atomics.py`: Refresh atomic tests from GitHub
- `validate_atomic.py`: Validate atomic test YAML
- `execute_atomic.py`: Execute atomic tests (optional)

### `src/utils/`

Utility functions:

- `config.py`: Configuration helpers (environment variables, paths)

## Data Flow

1. **Startup**:

   - `src/__main__.py` → `src/server/app.py` → Creates MCP server
   - Downloads atomics via `src/services/atomic_loader.py`
   - Loads atomics into memory

1. **Tool Calls**:

   - Client → MCP Server → Tool handler in `src/tools/`
   - Tools use services in `src/services/` for business logic
   - Services use models in `src/models/` for data validation

1. **Resource Access**:

   - Client → MCP Server → `src/server/resources.py`
   - Returns atomic test YAML files

## Design Principles

- **Separation of Concerns**: Each module has a single, well-defined responsibility
- **Layered Architecture**: Tools → Services → Models
- **Dependency Injection**: Context passed through FastMCP
- **Type Safety**: Pydantic models for runtime validation
- **Security**: Input validation, path traversal prevention, authentication support

## Adding New Features

### Adding a New Tool

1. Create `src/tools/my_tool.py`
1. Implement the tool function
1. Export from `src/tools/__init__.py`
1. Register in `src/server/app.py`

### Adding a New Service

1. Create `src/services/my_service.py`
1. Implement business logic
1. Export from `src/services/__init__.py`
1. Use in tools or other services

### Adding New Models

1. Add to `src/models/atomic.py` or create new file
1. Export from `src/models/__init__.py`
1. Use in services and tools
