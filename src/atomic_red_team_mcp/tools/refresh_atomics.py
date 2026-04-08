"""Refresh atomics tool."""

import asyncio

from fastmcp import Context
from fastmcp.dependencies import Progress

from atomic_red_team_mcp.models import RefreshAtomicsOutput
from atomic_red_team_mcp.services import create_index, download_atomics, load_atomics
from atomic_red_team_mcp.utils.config import get_settings


async def refresh_atomics(
    ctx: Context,
    progress: Progress = Progress(),
) -> RefreshAtomicsOutput:
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
        progress: Background task progress reporter (injected automatically)

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

    Notes:
        - This operation may take 30-60 seconds depending on network speed
        - Runs as a background task — the client receives a task ID immediately
          and can poll for completion
        - Requires internet connectivity to GitHub
        - Overwrites any local modifications to atomic tests
        - The repository is cloned with depth=1 for efficiency (only latest commit)
        - Failed YAML files are logged but don't stop the overall refresh
    """
    settings = get_settings()
    try:
        await progress.set_total(3)

        await progress.set_message("Downloading atomics from GitHub...")
        ctx.info("Starting atomic test download from GitHub")
        await asyncio.to_thread(download_atomics, force=True)
        await progress.increment()

        await progress.set_message("Loading atomic tests...")
        atomics = await asyncio.to_thread(load_atomics)
        await progress.increment()

        await progress.set_message("Updating server memory...")
        index = create_index(atomics)
        ctx.lifespan_context["atomics"] = atomics
        ctx.lifespan_context["index"] = index
        await progress.increment()

        message = f"Successfully refreshed {len(atomics)} atomics from {settings.github_repo_url}"
        ctx.info(message)

        return RefreshAtomicsOutput(
            success=True,
            message=message,
            atomics_count=len(atomics),
            repository_url=settings.github_repo_url,
        )
    except Exception as e:
        error_message = f"Failed to refresh atomics: {e}"
        ctx.warning(error_message)
        return RefreshAtomicsOutput(
            success=False,
            message=error_message,
            atomics_count=0,
            repository_url=settings.github_repo_url,
        )
