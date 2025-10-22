"""Configuration utilities."""

import os


def get_atomics_dir() -> str:
    """Get the atomics directory path from environment or default."""
    return os.getenv(
        "ART_DATA_DIR",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "atomics"),
    )
