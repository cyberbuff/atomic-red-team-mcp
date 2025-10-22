"""Refresh atomics tool."""

import logging

from fastmcp import Context

from atomic_red_team_mcp.services import download_atomics, load_atomics

logger = logging.getLogger(__name__)


async def refresh_atomics(ctx: Context):
    """Refresh atomics. Refresh local changes and save it to memory."""
    try:
        download_atomics(force=True)
        # Reload atomics into memory
        atomics = load_atomics()
        ctx.request_context.lifespan_context.atomics = atomics
        logger.info(f"Successfully refreshed {len(atomics)} atomics")
        return f"Successfully refreshed {len(atomics)} atomics"
    except Exception as e:
        logger.error(f"Failed to refresh atomics: {e}", exc_info=True)
        raise
