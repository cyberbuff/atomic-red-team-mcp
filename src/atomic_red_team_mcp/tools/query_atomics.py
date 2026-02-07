"""Query atomics tool."""

import logging
import re
import time
from typing import Optional

from fastmcp import Context

from atomic_red_team_mcp.models import QueryAtomicsOutput
from atomic_red_team_mcp.services import create_index

logger = logging.getLogger(__name__)


def query_atomics(
    ctx: Context,
    query: str,
    guid: Optional[str] = None,
    technique_id: Optional[str] = None,
    technique_name: Optional[str] = None,
    supported_platforms: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> QueryAtomicsOutput:
    """Search and filter atomic tests across the repository.

    This tool searches through all atomic tests and returns matches based on your
    criteria. You can search by free-text query, or filter by specific attributes like
    technique ID, GUID, or platform. Results are paginated for better performance.

    Args:
        query: Free-text search term to match against all atomic test fields including
               name, description, commands, and input arguments. Supports multi-word
               queries where all words must match (AND logic).
               Examples: "powershell registry", "credential access", "T1059"

        guid: Filter by exact atomic test GUID (UUID format).
              Example: "a8c41029-8d2a-4661-ab83-e5104c1cb667"
              Use this when you know the specific test you want to retrieve.

        technique_id: Filter by MITRE ATT&CK technique ID. Must follow the format
                      T#### or T####.### (e.g., T1059, T1059.001).
                      Example: "T1059.001" for PowerShell technique
                      Returns all atomic tests associated with this technique.

        technique_name: Filter by technique name (case-insensitive partial match).
                        Example: "Command and Scripting Interpreter"
                        Useful when you know the technique name but not the ID.

        supported_platforms: Filter by platform (case-insensitive partial match).
                            Valid platforms: windows, linux, macos, office-365, azure-ad,
                            google-workspace, saas, iaas, containers, iaas:aws, iaas:azure,
                            iaas:gcp, esxi
                            Example: "windows", "linux", "macos"

        limit: Maximum number of results to return (default: 20, max: 100).
               Use pagination to retrieve more results.

        offset: Number of results to skip (default: 0).
                Use with limit for pagination through large result sets.

    Returns:
        QueryAtomicsOutput: Structured output containing:
            - total_results: Total number of matching atomic tests
            - returned_count: Number of results in this response
            - atomics: List of matching atomic tests
            - has_more: Whether more results are available
            - next_offset: Offset for next page (if has_more is True)
            - query_metadata: Information about applied filters

    Examples:
        # Find all PowerShell-related tests (first 20)
        query_atomics(ctx, query="powershell")

        # Get next page of results
        query_atomics(ctx, query="powershell", limit=20, offset=20)

        # Find all Windows registry tests
        query_atomics(ctx, query="registry", supported_platforms="windows")

        # Find specific technique
        query_atomics(ctx, query="", technique_id="T1059.001")

        # Find test by GUID
        query_atomics(ctx, query="", guid="a8c41029-8d2a-4661-ab83-e5104c1cb667")

    Raises:
        ValueError: If query is empty or exceeds 1000 characters
        ValueError: If technique_id format is invalid (must be T#### or T####.###)
        ValueError: If limit is less than 1 or greater than 100
        ValueError: If offset is negative
    """
    try:
        # Input validation - allow empty query if using filters
        if (not query or not query.strip()) and not (
            guid or technique_id or technique_name or supported_platforms
        ):
            raise ValueError(
                "Query parameter cannot be empty without filters. "
                "Examples: query='powershell registry' to find PowerShell tests related to registry, "
                "or use filters like technique_id='T1059.001' to search by MITRE ATT&CK technique."
            )

        if query and len(query) > 1000:  # Prevent extremely long queries
            raise ValueError(
                "Query too long (max 1000 characters). "
                "Please shorten your search query or use specific filters like technique_id or guid."
            )

        # Validate pagination parameters
        if limit < 1 or limit > 100:
            raise ValueError(
                f"Invalid limit: {limit}. Limit must be between 1 and 100. "
                "Use pagination (offset parameter) to retrieve more results."
            )

        if offset < 0:
            raise ValueError(f"Invalid offset: {offset}. Offset must be 0 or greater.")

        # Validate technique_id format if provided
        if technique_id and not re.match(r"^T\d{4}(?:\.\d{3})?$", technique_id):
            raise ValueError(
                f"Invalid technique ID format: {technique_id}. "
                "Must follow the format T#### or T####.### (e.g., T1059 or T1059.001)"
            )

        start_time = time.time()
        atomics = ctx.request_context.lifespan_context.atomics

        if not atomics:
            logger.warning("No atomics loaded in memory")
            return QueryAtomicsOutput(
                total_results=0,
                returned_count=0,
                atomics=[],
                has_more=False,
                next_offset=None,
                query_metadata={"query": query, "filters_applied": []},
            )

        # Create index for fast lookups
        index = create_index(atomics)
        logger.debug(f"Index stats: {index.stats()}")

        # Apply filters using index for performance
        if guid:
            # O(1) lookup by GUID
            atomic = index.get_by_guid(guid)
            atomics = [atomic] if atomic else []
            logger.debug(f"GUID lookup took {time.time() - start_time:.4f}s")
        elif technique_id:
            # O(1) lookup by technique_id
            atomics = index.get_by_technique_id(technique_id)
            logger.debug(f"Technique ID lookup took {time.time() - start_time:.4f}s")
        elif supported_platforms:
            # Indexed platform lookup
            atomics = index.get_by_platform(supported_platforms)
            logger.debug(f"Platform lookup took {time.time() - start_time:.4f}s")

        # Apply technique_name filter if needed (after other filters)
        if technique_name:
            atomics = [
                atomic
                for atomic in atomics
                if technique_name.lower() in (atomic.technique_name or "").lower()
            ]

        # Apply text search if query is provided
        if query and query.strip():
            query_lower = query.strip().lower()
            matching_atomics = []

            for atomic in atomics:
                if all(
                    query_word in str(atomic.model_dump()).lower()
                    for query_word in query_lower.split(" ")
                ):
                    matching_atomics.append(atomic)
        else:
            # No text search, use filtered results
            matching_atomics = atomics

        # Calculate pagination
        total_results = len(matching_atomics)
        paginated_atomics = matching_atomics[offset : offset + limit]
        returned_count = len(paginated_atomics)
        has_more = offset + limit < total_results
        next_offset = offset + limit if has_more else None

        # Build query metadata
        query_metadata = {"query": query, "filters_applied": []}
        if guid:
            query_metadata["filters_applied"].append(f"guid={guid}")
        if technique_id:
            query_metadata["filters_applied"].append(f"technique_id={technique_id}")
        if technique_name:
            query_metadata["filters_applied"].append(f"technique_name={technique_name}")
        if supported_platforms:
            query_metadata["filters_applied"].append(f"platform={supported_platforms}")

        logger.info(
            f"Query '{query}' with filters {query_metadata['filters_applied']} "
            f"returned {total_results} total results, showing {returned_count} "
            f"(offset={offset}, limit={limit})"
        )

        return QueryAtomicsOutput(
            total_results=total_results,
            returned_count=returned_count,
            atomics=paginated_atomics,
            has_more=has_more,
            next_offset=next_offset,
            query_metadata=query_metadata,
        )

    except Exception as e:
        logger.error(f"Error in query_atomics: {e}")
        raise
