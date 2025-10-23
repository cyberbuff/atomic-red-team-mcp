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
    """Search and filter atomic tests across the repository.

    This tool searches through all atomic tests and returns matches based on your
    criteria. You can search by free-text query, or filter by specific attributes like
    technique ID, GUID, or platform.

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

    Returns:
        List[MetaAtomic]: A list of matching atomic tests. Each test includes:
            - name: Descriptive name of the test
            - description: Detailed explanation of what the test does
            - technique_id: Associated MITRE ATT&CK technique ID
            - technique_name: Human-readable technique name
            - supported_platforms: List of platforms where test can run
            - executor: Execution details (command, cleanup, etc.)
            - input_arguments: Configurable parameters for the test
            - auto_generated_guid: Unique identifier for the test

    Examples:
        # Find all PowerShell-related tests
        query_atomics(ctx, query="powershell")

        # Find all Windows registry tests
        query_atomics(ctx, query="registry", supported_platforms="windows")

        # Find specific technique
        query_atomics(ctx, query="", technique_id="T1059.001")

        # Find test by GUID
        query_atomics(ctx, query="", guid="a8c41029-8d2a-4661-ab83-e5104c1cb667")

    Raises:
        ValueError: If query is empty or exceeds 1000 characters
        ValueError: If technique_id format is invalid (must be T#### or T####.###)
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
