"""Authentication configuration for MCP server."""

import logging

from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

from atomic_red_team_mcp.utils.config import get_settings

logger = logging.getLogger(__name__)


def configure_auth():
    """Configure authentication based on settings.

    Returns:
        StaticTokenVerifier if auth_token is configured, None otherwise.
    """
    settings = get_settings()

    if not settings.is_auth_enabled:
        logger.info("Authentication disabled - no auth token configured")
        return None

    verifier = StaticTokenVerifier(
        tokens={
            settings.auth_token: {
                "client_id": settings.auth_client_id,
                "scopes": settings.auth_scopes,
            }
        },
        required_scopes=["read"],
    )
    logger.info(
        f"Static token authentication enabled for client: {settings.auth_client_id}"
    )
    return verifier
