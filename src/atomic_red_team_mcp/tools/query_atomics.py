"""Query atomics tool."""

import re
import time
from typing import Optional

from fastmcp import Context
from fastmcp.utilities.pagination import paginate_sequence

from atomic_red_team_mcp.models import QueryAtomicsOutput
from atomic_red_team_mcp.services import AtomicIndex

_DEFAULT_PAGE_SIZE = 50
_MAX_PAGE_SIZE = 200


def query_atomics(
    ctx: Context,
    query: str,
    guid: Optional[str] = None,
    technique_id: Optional[str] = None,
    technique_name: Optional[str] = None,
    supported_platforms: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = _DEFAULT_PAGE_SIZE,
) -> QueryAtomicsOutput:
    """Search and filter atomic tests across the repository.

    This tool searches through all atomic tests and returns matches based on your
    criteria. You can search by free-text query, or filter by specific attributes like
    technique ID, GUID, or platform. Results are paginated — use the returned
    `next_cursor` to fetch subsequent pages.

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

        cursor: Opaque pagination cursor returned by a previous call as `next_cursor`.
                Omit or pass null to start from the first page.

        limit: Maximum number of results to return per page (1–200, default 50).

    Returns:
        QueryAtomicsOutput: Structured output containing:
            - total_results: Total number of matching atomic tests
            - atomics: List of matching atomic tests for this page
            - next_cursor: Opaque cursor for the next page, or null if last page
            - query_metadata: Information about applied filters

    Raises:
        ValueError: If query is empty without any filters
        ValueError: If query exceeds 1000 characters
        ValueError: If technique_id format is invalid (must be T#### or T####.###)
        ValueError: If limit is outside the range 1–200
        ValueError: If cursor is malformed
    """
    if (not query or not query.strip()) and not (
        guid or technique_id or technique_name or supported_platforms
    ):
        raise ValueError(
            "Query parameter cannot be empty without filters. "
            "Examples: query='powershell registry' to find PowerShell tests related to registry, "
            "or use filters like technique_id='T1059.001' to search by MITRE ATT&CK technique."
        )

    if query and len(query) > 1000:
        raise ValueError(
            "Query too long (max 1000 characters). "
            "Please shorten your search query or use specific filters like technique_id or guid."
        )

    if not (1 <= limit <= _MAX_PAGE_SIZE):
        raise ValueError(f"limit must be between 1 and {_MAX_PAGE_SIZE}")

    if technique_id and not re.match(r"^T\d{4}(?:\.\d{3})?$", technique_id):
        raise ValueError(
            f"Invalid technique ID format: {technique_id}. "
            "Must follow the format T#### or T####.### (e.g., T1059 or T1059.001)"
        )

    start_time = time.time()
    atomics = ctx.lifespan_context.get("atomics", [])
    index: AtomicIndex | None = ctx.lifespan_context.get("index")

    if not atomics or index is None:
        ctx.debug("No atomics loaded in memory")
        return QueryAtomicsOutput(
            total_results=0,
            atomics=[],
            next_cursor=None,
            query_metadata={"query": query, "filters_applied": []},
        )

    ctx.debug(f"Index stats: {index.stats()}")

    # Apply indexed filters for O(1) lookups
    if guid:
        atomic = index.get_by_guid(guid)
        atomics = [atomic] if atomic else []
        ctx.debug(f"GUID lookup took {time.time() - start_time:.4f}s")
    elif technique_id:
        atomics = index.get_by_technique_id(technique_id)
        ctx.debug(f"Technique ID lookup took {time.time() - start_time:.4f}s")
    elif supported_platforms:
        atomics = index.get_by_platform(supported_platforms)
        ctx.debug(f"Platform lookup took {time.time() - start_time:.4f}s")

    if technique_name:
        atomics = [
            a
            for a in atomics
            if technique_name.lower() in (a.technique_name or "").lower()
        ]

    if query and query.strip():
        atomics = index.search_text(atomics, query.strip().lower().split())

    total_results = len(atomics)
    page, next_cursor = paginate_sequence(atomics, cursor, limit)

    query_metadata: dict = {"query": query, "filters_applied": []}
    if guid:
        query_metadata["filters_applied"].append(f"guid={guid}")
    if technique_id:
        query_metadata["filters_applied"].append(f"technique_id={technique_id}")
    if technique_name:
        query_metadata["filters_applied"].append(f"technique_name={technique_name}")
    if supported_platforms:
        query_metadata["filters_applied"].append(f"platform={supported_platforms}")

    ctx.info(
        f"Query '{query}' with filters {query_metadata['filters_applied']} "
        f"returned {total_results} total, showing {len(page)}"
    )

    return QueryAtomicsOutput(
        total_results=total_results,
        atomics=page,
        next_cursor=next_cursor,
        query_metadata=query_metadata,
    )
