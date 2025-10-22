"""Service for loading and downloading Atomic Red Team tests."""

import glob
import logging
import os
import shutil
import tempfile
from typing import List

import git
import yaml

from atomic_red_team_mcp.models import MetaAtomic, Technique
from atomic_red_team_mcp.utils.config import get_atomics_dir

logger = logging.getLogger(__name__)


def download_atomics(force=False) -> None:
    """Download Atomic Red Team atomics from GitHub repository."""
    atomics_dir = get_atomics_dir()
    repo_url = os.getenv("ART_GITHUB_URL", "https://github.com")
    repo_owner = os.getenv("ART_GITHUB_USER", "redcanaryco")
    repo_name = os.getenv("ART_GITHUB_REPO", "atomic-red-team")

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
    atomics_dir = get_atomics_dir()
    atomics = []

    for file in glob.glob(f"{atomics_dir}/T*/T*.yaml"):
        with open(file, "r", encoding="utf-8", errors="replace") as f:
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
