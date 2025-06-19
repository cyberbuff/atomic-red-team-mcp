"""
Atomic Red Team MCP Server

An MCP server that provides access to Atomic Red Team tests for security professionals.
"""

import glob
import logging
import os
import shutil
import tempfile
import re

import git
import yaml
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import List, Optional

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

from models import Atomic, Technique, MetaAtomic

# Configure logging to stderr to avoid interfering with MCP JSON protocol
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    atomics: List[MetaAtomic]


def download_atomics(force=False) -> None:
    """Download Atomic Red Team atomics from GitHub repository."""
    atomics_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "atomics")

    repo_url = os.getenv("GITHUB_URL", "https://github.com")
    repo_owner = os.getenv("GITHUB_USER", "redcanaryco")
    repo_name = os.getenv("GITHUB_REPO", "atomic-red-team")

    if force:
        shutil.rmtree(atomics_dir, ignore_errors=True)

    # Check if atomics directory already exists
    if os.path.exists(atomics_dir):
        logger.info(f"Atomics directory already exists at {atomics_dir}")
        return

    logger.info("Downloading Atomic Red Team atomics...")

    # Use system temp directory instead of current working directory
    with tempfile.TemporaryDirectory(prefix="atomic_repo_") as temp_repo_dir:
        try:
            # Clone the repository with depth 1 to get only the latest version
            git.Repo.clone_from(
                f"{repo_url}/{repo_owner}/{repo_name}.git", temp_repo_dir, depth=1
            )

            # Move only the atomics directory
            source_atomics = os.path.join(temp_repo_dir, "atomics")
            if os.path.exists(source_atomics):
                shutil.move(source_atomics, atomics_dir)
            else:
                raise Exception("Atomics directory not found in repository")

            logger.info(f"Successfully downloaded atomics to {atomics_dir}")

        except Exception as e:
            logger.error(f"Error downloading atomics: {e}")
            raise


def load_atomics() -> List[MetaAtomic]:
    """Load atomics from the atomics directory."""
    atomics_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "atomics")
    atomics = []

    for file in glob.glob(f"{atomics_path}/T*/T*.yaml"):
        with open(file, "r") as f:
            content = f.read()
        try:
            # Parse YAML content
            yaml_data = yaml.safe_load(content)
            # Create Technique instance with parsed data
            technique = Technique(**yaml_data)
            atomics.extend(technique.atomic_tests)
        except Exception as e:
            logger.error(f"Error loading atomic test from {file}: {e}")
            continue
    return atomics


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context."""
    # Download atomics on startup
    try:
        download_atomics()
        atomics = load_atomics()
        yield AppContext(atomics=atomics)
    finally:
        pass


# Create an MCP server
# Configure for Docker deployment with host binding
host = os.getenv("MCP_HOST", "0.0.0.0")
port = int(os.getenv("MCP_PORT", "8000"))

mcp = FastMCP(
    "Atomic Red Team MCP",
    instructions="""Use this MCP server to access and create Atomic Red Team tests for security testing.

AVAILABLE TOOLS:
- `query_atomics`: Search existing atomic tests by technique ID, name, description, or platform
- `refresh_atomics`: Update atomic tests from GitHub repository
- `get_validation_schema`: Get the JSON schema for atomic test structure
- `validate_atomic`: Validate atomic test YAML against the schema

CREATING NEW ATOMIC TESTS:
When creating atomic tests, you are acting as an Offensive Security expert. Follow these best practices:

🎯 CORE REQUIREMENTS:
- Design tests that mirror actual adversary behavior and real-world attack patterns
- Always validate tests using `validate_atomic` tool before finalizing
- Use `get_validation_schema` first to understand the required structure
- Keep external dependencies to a minimum for better portability and reliability

🧹 SYSTEM SAFETY:
- Always include cleanup commands to restore the system to its original state if needed
- Ensure tests are fully functional and can be executed without errors
- Search online if needed to find manpages/documentation for tools used

📝 DOCUMENTATION STANDARDS:
- Use clear, descriptive names that indicate the technique being tested
- Provide comprehensive descriptions explaining what the test does and why
- Include external references if you used any online resources
- Clearly document any required tools, permissions, or system configurations
- If there are no prerequisites, omit the dependencies section

⚙️ IMPLEMENTATION BEST PRACTICES:
- Use parameterized inputs (input_arguments) for flexibility and reusability
- If there are no input arguments, omit the input_arguments section
- Do NOT use hardcoded values in commands - use input_arguments instead
- Do NOT include echo commands or print statements in the test commands
- Set elevation_required: true if using sudo or admin privileges
- Keep tests concise and focused on the specific technique being tested
- Do not create unnecessary files for saving output unless required for the test
- Do not add auto_generated_guid to the atomic test for new tests

WORKFLOW FOR CREATING ATOMIC TESTS:
1. Call `get_validation_schema` to understand the atomic test structure
2. Create the atomic test following the schema and best practices above
3. Call `validate_atomic` tool with the generated YAML to ensure it's valid
4. If validation fails, fix the issues and validate again until successful
""",
    lifespan=app_lifespan,
    host=host,
    port=port,
)


@mcp.resource("file://documents/{technique_id}")
def read_document(technique_id: str) -> str:
    """Read a atomic test file by technique ID.
    Args:
        technique_id: The technique ID of the atomic.
    """
    # Input validation to prevent path traversal
    if not re.match(r"^T\d{4}(?:\.\d{3})?$", technique_id):
        raise ValueError(f"Invalid technique ID format: {technique_id}")

    atomics_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "atomics")
    file_path = os.path.join(atomics_path, technique_id, f"{technique_id}.yaml")

    # Ensure the file path is within the atomics directory (security check)
    if not file_path.startswith(atomics_path):
        raise ValueError(f"Invalid file path: {technique_id}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Atomic test not found for Technique ID {technique_id}"
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except (IOError, OSError) as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


@mcp.tool()
async def refresh_atomics(ctx: Context[ServerSession, AppContext]):
    """Refresh atomics. Download latest atomics from GitHub."""
    try:
        download_atomics(force=True)
        # Reload atomics into memory
        atomics = load_atomics()
        ctx.request_context.lifespan_context.atomics = atomics
        logger.info(f"Successfully refreshed {len(atomics)} atomics")
        return f"Successfully refreshed {len(atomics)} atomics"
    except Exception as e:
        logger.error(f"Failed to refresh atomics: {e}")
        raise RuntimeError(f"Failed to refresh atomics: {e}")


@mcp.tool()
def query_atomics(
    ctx: Context[ServerSession, AppContext],
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
            # Search in atomic name and description
            if (
                query_lower in atomic.name.lower()
                or query_lower in atomic.description.lower()
                or (
                    atomic.technique_name
                    and query_lower in atomic.technique_name.lower()
                )
            ):
                matching_atomics.append(atomic)

        logger.info(f"Query '{query}' returned {len(matching_atomics)} results")
        return matching_atomics

    except Exception as e:
        logger.error(f"Error in query_atomics: {e}")
        raise


@mcp.tool()
def get_validation_schema() -> dict:
    """Get the JSON schema that defines the structure and requirements for atomic tests.
    
    This schema defines all required and optional fields for creating valid atomic tests.
    Use this to understand what fields are needed when creating a new atomic test.
    The schema follows the official Atomic Red Team format.
    
    Returns:
        A JSON schema dictionary containing field definitions, types, and validation rules.
    """
    return Atomic.model_json_schema()


@mcp.tool()
def validate_atomic(yaml_string: str) -> dict:
    """Validate an atomic test YAML string against the official Atomic Red Team schema.
    
    This tool checks if your atomic test follows the correct structure and includes all
    required fields. Use this before finalizing any atomic test to ensure it meets
    the quality standards and can be properly parsed by Atomic Red Team tools.

    Args:
        yaml_string: The complete YAML string of the atomic test to validate.
                    Should include all fields like name, description, supported_platforms,
                    executor, etc. as defined in the schema.

    Returns:
        Dictionary with validation result containing:
        - valid (bool): Whether the atomic test is valid
        - message/error (str): Success message or detailed error information
        - atomic_name (str): Name of the atomic test (if valid)
        - supported_platforms (list): Platforms the test supports (if valid)
    """
    try:
        if not yaml_string or not yaml_string.strip():
            return {"valid": False, "error": "YAML string cannot be empty"}

        # Parse YAML
        try:
            atomic_data = yaml.safe_load(yaml_string)
        except yaml.YAMLError as e:
            return {"valid": False, "error": f"Invalid YAML format: {e}"}

        if not atomic_data:
            return {"valid": False, "error": "YAML parsed to empty data"}

        # Validate with Pydantic model
        try:
            atomic = Atomic(**atomic_data)
            return {
                "valid": True,
                "message": "Atomic test validation successful",
                "atomic_name": atomic.name,
                "supported_platforms": atomic.supported_platforms,
            }
        except Exception as validation_error:
            return {"valid": False, "error": f"Validation error: {validation_error}"}

    except Exception as e:
        logger.error(f"Unexpected error in validate_atomic: {e}")
        return {"valid": False, "error": f"Unexpected validation error: {e}"}


def main():
    """Main entry point for the CLI."""
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()

