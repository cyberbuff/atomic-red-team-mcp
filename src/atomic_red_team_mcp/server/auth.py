"""Authentication configuration for MCP server."""

import logging
import os

from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

logger = logging.getLogger(__name__)


def configure_auth():
    """Configure authentication based on environment variables.

    Returns:
        StaticTokenVerifier if ART_AUTH_TOKEN is set, None otherwise.
    """
    auth_token = os.getenv("ART_AUTH_TOKEN")

    if not auth_token:
        logger.info("No ART_AUTH_TOKEN configured - authentication disabled")
        return None

    # Configure static token verifier with the token from environment
    # Extract optional client_id and scopes from environment
    client_id = os.getenv("ART_AUTH_CLIENT_ID", "dev-client")
    scopes_str = os.getenv("ART_AUTH_SCOPES", "read, admin")
    scopes = [s.strip() for s in scopes_str.split(",") if s.strip()]

    verifier = StaticTokenVerifier(
        tokens={auth_token: {"client_id": client_id, "scopes": scopes}},
        required_scopes=["read"],
    )
    logger.info(f"Static token authentication enabled for client: {client_id}")
    return verifier
