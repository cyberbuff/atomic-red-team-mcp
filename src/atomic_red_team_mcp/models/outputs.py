"""Output schemas for MCP tool responses."""

from typing import List, Optional

from pydantic import BaseModel, Field

from atomic_red_team_mcp.models.atomic import MetaAtomic, Platform


class QueryAtomicsOutput(BaseModel):
    """Structured output for query_atomics tool.

    Provides pagination metadata and clear result counts to help LLMs
    understand the scope of results and whether more data is available.
    """

    total_results: int = Field(
        description="Total number of atomic tests matching the query"
    )
    returned_count: int = Field(
        description="Number of atomic tests returned in this response"
    )
    atomics: List[MetaAtomic] = Field(description="List of matching atomic tests")
    has_more: bool = Field(
        description="Whether more results are available beyond this page"
    )
    next_offset: Optional[int] = Field(
        default=None,
        description="Offset value to use for retrieving the next page of results",
    )
    query_metadata: dict = Field(
        default_factory=dict,
        description="Metadata about the query execution (filters applied, etc.)",
    )


class ValidationOutput(BaseModel):
    """Structured output for validate_atomic tool.

    Provides clear validation status with warnings and errors separated
    for better LLM comprehension and decision-making.
    """

    valid: bool = Field(
        description="Whether the atomic test passed structural validation"
    )
    message: str = Field(
        description="Human-readable validation message with warnings prominently displayed"
    )
    atomic_name: Optional[str] = Field(
        default=None, description="Name of the atomic test (only if valid)"
    )
    supported_platforms: Optional[List[Platform]] = Field(
        default=None, description="Platforms the test supports (only if valid)"
    )
    warnings: Optional[List[str]] = Field(
        default=None,
        description="List of best practice warnings that should be addressed",
    )
    error: Optional[str] = Field(
        default=None, description="Detailed error message (only if invalid)"
    )


class RefreshAtomicsOutput(BaseModel):
    """Structured output for refresh_atomics tool.

    Provides details about the refresh operation for better tracking.
    """

    success: bool = Field(
        description="Whether the refresh operation completed successfully"
    )
    message: str = Field(
        description="Human-readable message about the refresh operation"
    )
    atomics_count: int = Field(
        description="Number of atomic tests loaded after refresh"
    )
    repository_url: str = Field(
        description="GitHub repository URL that was used for refresh"
    )


class ServerInfoOutput(BaseModel):
    """Structured output for server_info tool.

    Provides comprehensive server metadata for debugging and compatibility checks.
    """

    name: str = Field(description="Server name")
    version: str = Field(description="Server version number")
    transport: str = Field(
        description="MCP transport protocol being used (stdio, sse, streamable-http)"
    )
    os: str = Field(description="Operating system platform (Darwin, Linux, Windows)")
    data_directory: str = Field(
        description="Absolute path to atomic tests storage directory"
    )
    execution_enabled: bool = Field(
        description="Whether atomic test execution is enabled on this server"
    )


class ExecuteAtomicOutput(BaseModel):
    """Structured output for execute_atomic tool.

    Provides detailed execution results including stdout, stderr, and status.
    """

    success: bool = Field(description="Whether the atomic test executed successfully")
    atomic_name: str = Field(description="Name of the executed atomic test")
    technique_id: str = Field(description="MITRE ATT&CK technique ID")
    platform: str = Field(description="Platform the test was executed on")
    execution_time: float = Field(description="Execution time in seconds")
    stdout: str = Field(
        default="", description="Standard output from the test execution"
    )
    stderr: str = Field(
        default="", description="Standard error from the test execution"
    )
    exit_code: Optional[int] = Field(
        default=None, description="Exit code from the executed command"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if execution failed"
    )
