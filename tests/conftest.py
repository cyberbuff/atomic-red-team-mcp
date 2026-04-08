"""Shared pytest fixtures and configuration."""

import pytest


@pytest.fixture
def anyio_backend():
    """Use asyncio as the only anyio backend for async tests."""
    return "asyncio"
