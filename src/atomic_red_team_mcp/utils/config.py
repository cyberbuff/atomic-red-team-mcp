"""Configuration management using Pydantic Settings."""

import os
from functools import lru_cache
from typing import List, Optional

from fastmcp.server.server import Transport
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation and environment variable support.

    All settings can be configured via environment variables with the ART_ prefix.
    Settings can also be loaded from a .env file in the project root.
    """

    model_config = SettingsConfigDict(
        env_prefix="ART_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )

    # Server Configuration
    mcp_transport: Transport = Field(
        default="stdio",
        description="Transport protocol for MCP communication",
    )
    mcp_host: str = Field(
        default="0.0.0.0",
        description="Server host address for HTTP/SSE transports",
    )
    mcp_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port number for HTTP/SSE transports",
    )

    # Data Directory Configuration
    data_dir: str = Field(
        default_factory=lambda: os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "atomics"
        ),
        description="Local directory path where atomic test files are stored",
    )

    # GitHub Repository Configuration
    github_url: str = Field(
        default="https://github.com",
        description="GitHub URL for atomics repository",
    )
    github_user: str = Field(
        default="redcanaryco",
        description="GitHub user/organization name",
    )
    github_repo: str = Field(
        default="atomic-red-team",
        description="GitHub repository name",
    )

    # Security Configuration
    execution_enabled: bool = Field(
        default=False,
        description="Enable the execute_atomic tool. WARNING: Only enable in controlled environments.",
    )

    # Authentication Configuration
    auth_token: Optional[str] = Field(
        default=None,
        description="Static bearer token for authentication. If not set, authentication is disabled.",
    )
    auth_client_id: str = Field(
        default="authorized-client",
        description="Client identifier for authenticated requests",
    )
    auth_scopes: List[str] = Field(
        default=["read", "admin"],
        description="List of OAuth scopes for authentication",
    )

    @field_validator("execution_enabled", mode="before")
    @classmethod
    def parse_execution_enabled(cls, v):
        """Parse execution_enabled from various string formats."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ["true", "1", "yes"]
        return bool(v)

    @field_validator("auth_scopes", mode="before")
    @classmethod
    def parse_auth_scopes(cls, v):
        """Parse auth_scopes from comma-separated string or list."""
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @field_validator("mcp_transport")
    @classmethod
    def validate_transport(cls, v):
        """Validate transport is a supported value."""
        valid_transports = ["stdio", "sse", "streamable-http"]
        if v not in valid_transports:
            raise ValueError(
                f"Invalid transport '{v}'. Must be one of {valid_transports}"
            )
        return v

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, v):
        """Validate GitHub URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("GitHub URL must start with http:// or https://")
        return v.rstrip("/")  # Remove trailing slash

    @property
    def is_http_transport(self) -> bool:
        """Check if using HTTP-based transport."""
        return self.mcp_transport == "streamable-http"

    @property
    def is_auth_enabled(self) -> bool:
        """Check if authentication is enabled."""
        return self.auth_token is not None

    @property
    def github_repo_url(self) -> str:
        """Get full GitHub repository URL."""
        return f"{self.github_url}/{self.github_user}/{self.github_repo}.git"

    def get_atomics_dir(self) -> str:
        """Get the atomics directory path.

        Returns:
            Absolute path to the atomics directory.
        """
        return os.path.abspath(self.data_dir)


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    This function is cached to ensure settings are loaded only once
    during the application lifetime.

    Returns:
        Settings instance with validated configuration.
    """
    return Settings()


# Legacy function for backward compatibility
def get_atomics_dir() -> str:
    """Get the atomics directory path from settings.

    This function maintains backward compatibility with existing code.

    Returns:
        Absolute path to the atomics directory.
    """
    return get_settings().get_atomics_dir()
