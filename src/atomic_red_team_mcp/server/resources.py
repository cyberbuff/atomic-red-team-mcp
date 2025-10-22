"""MCP resource handlers."""

import logging
import os
import re

logger = logging.getLogger(__name__)


def read_atomic_document(technique_id: str, atomics_dir: str) -> str:
    """Read a atomic test file by technique ID.
    Args:
        technique_id: The technique ID of the atomic.
        atomics_dir: The directory containing atomic test files.
    """
    # Input validation to prevent path traversal
    if not re.match(r"^T\d{4}(?:\.\d{3})?$", technique_id):
        raise ValueError(f"Invalid technique ID format: {technique_id}")

    file_path = os.path.join(atomics_dir, technique_id, f"{technique_id}.yaml")

    # Ensure the file path is within the atomics directory (security check)
    if not file_path.startswith(atomics_dir):
        raise ValueError(f"Invalid file path: {technique_id}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Atomic test not found for Technique ID {technique_id}"
        )

    try:
        # Normalize path for Windows compatibility
        normalized_path = os.path.normpath(file_path)
        with open(normalized_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return content
    except (IOError, OSError) as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise
