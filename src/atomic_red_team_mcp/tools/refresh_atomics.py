"""Refresh atomics tool."""

import logging

from fastmcp import Context

from atomic_red_team_mcp.models import RefreshAtomicsOutput
from atomic_red_team_mcp.services import download_atomics, load_atomics
from atomic_red_team_mcp.utils.config import get_settings

logger = logging.getLogger(__name__)


async def refresh_atomics(ctx: Context) -> RefreshAtomicsOutput:
    """Download and reload atomic tests from the GitHub repository.

    This tool forces a fresh download of all atomic tests from the configured GitHub
    repository, replacing any existing local copies. It then reloads all tests into
    memory, making them immediately available for querying and execution.

    Use this tool when:
    - You want to get the latest atomic tests from the repository
    - Custom atomic tests were added to the data directory
    - The atomic test database needs to be refreshed
    - You suspect the loaded tests are out of sync with the repository

    Args:
        ctx: MCP context (provided automatically by the framework)

    Returns:
        RefreshAtomicsOutput: Structured output containing:
            - success (bool): Whether the refresh operation completed successfully
            - message (str): Human-readable message about the refresh operation
            - atomics_count (int): Number of atomic tests loaded after refresh
            - repository_url (str): GitHub repository URL that was used for refresh

    Process:
        1. Deletes existing atomic tests directory (if present)
        2. Clones the GitHub repository (configured via ART_GITHUB_* settings)
        3. Extracts the atomics directory from the repository
        4. Parses all YAML files and validates them
        5. Loads atomic tests into server memory
        6. Makes tests immediately available to other tools

    Configuration:
        The repository location is controlled by environment variables:
        - ART_GITHUB_URL: Base GitHub URL (default: https://github.com)
        - ART_GITHUB_USER: User/organization (default: redcanaryco)
        - ART_GITHUB_REPO: Repository name (default: atomic-red-team)
        - ART_DATA_DIR: Local storage path (default: ./atomics)

    Examples:
        # Refresh from default repository
        refresh_atomics(ctx)

        # After setting custom repo in .env:
        # ART_GITHUB_USER=your-org
        # ART_GITHUB_REPO=custom-atomics
        refresh_atomics(ctx)

    Raises:
        Exception: If Git clone fails (network issues, invalid repository)
        Exception: If atomic test parsing fails (invalid YAML format)
        Exception: If disk space is insufficient for repository clone

    Notes:
        - This operation may take 30-60 seconds depending on network speed
        - Requires internet connectivity to GitHub
        - Overwrites any local modifications to atomic tests
        - The repository is cloned with depth=1 for efficiency (only latest commit)
        - Failed YAML files are logged but don't stop the overall refresh
    """
    settings = get_settings()
    try:
        download_atomics(force=True)
        # Reload atomics into memory
        atomics = load_atomics()
        ctx.request_context.lifespan_context.atomics = atomics

        message = f"Successfully refreshed {len(atomics)} atomics from {settings.github_repo_url}"
        logger.info(message)

        return RefreshAtomicsOutput(
            success=True,
            message=message,
            atomics_count=len(atomics),
            repository_url=settings.github_repo_url,
        )
    except Exception as e:
        error_message = f"Failed to refresh atomics: {e}"
        logger.error(error_message, exc_info=True)
        return RefreshAtomicsOutput(
            success=False,
            message=error_message,
            atomics_count=0,
            repository_url=settings.github_repo_url,
        )
