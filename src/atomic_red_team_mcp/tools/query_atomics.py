"""Query atomics tool."""

import logging
import re
from typing import List, Optional

from fastmcp import Context

from atomic_red_team_mcp.models import MetaAtomic

logger = logging.getLogger(__name__)


def query_atomics(
    ctx: Context,
    query: str,
    guid: Optional[str] = None,
    technique_id: Optional[str] = None,
    technique_name: Optional[str] = None,
    supported_platforms: Optional[str] = None,
) -> List[MetaAtomic]:
    """Search atomics by technique ID, name, description, or platform.
    Args:
        query: Search using a generic search term.
        guid: The GUID of the atomic.
        technique_id: The technique ID of the atomic.
        technique_name: The technique name of the atomic.
        supported_platforms: The supported platforms of the atomic.
    Returns:
        A list of matching atomics.
    """
    try:
        # Input validation
        if not query or not query.strip():
            raise ValueError("Query parameter cannot be empty")

        if len(query) > 1000:  # Prevent extremely long queries
            raise ValueError("Query too long (max 1000 characters)")

        # Validate technique_id format if provided
        if technique_id and not re.match(r"^T\d{4}(?:\.\d{3})?$", technique_id):
            raise ValueError(f"Invalid technique ID format: {technique_id}")

        atomics = ctx.request_context.lifespan_context.atomics

        if not atomics:
            logger.warning("No atomics loaded in memory")
            return []

        # Apply filters
        if supported_platforms:
            atomics = [
                atomic
                for atomic in atomics
                if any(
                    supported_platforms.lower() in platform.lower()
                    for platform in atomic.supported_platforms
                )
            ]

        if guid:
            atomics = [
                atomic for atomic in atomics if str(atomic.auto_generated_guid) == guid
            ]

        if technique_id:
            atomics = [
                atomic for atomic in atomics if atomic.technique_id == technique_id
            ]

        if technique_name:
            atomics = [
                atomic
                for atomic in atomics
                if technique_name.lower() in (atomic.technique_name or "").lower()
            ]

        query_lower = query.strip().lower()
        matching_atomics = []

        for atomic in atomics:
            if all(
                query_word in str(atomic.model_dump()).lower()
                for query_word in query_lower.split(" ")
            ):
                matching_atomics.append(atomic)

        logger.info(f"Query '{query}' returned {len(matching_atomics)} results")
        return matching_atomics

    except Exception as e:
        logger.error(f"Error in query_atomics: {e}")
        raise
