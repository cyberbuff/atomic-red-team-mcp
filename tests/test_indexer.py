"""Tests for atomic indexer performance optimizations."""

import uuid

import pytest

from atomic_red_team_mcp.models import MetaAtomic
from atomic_red_team_mcp.models.atomic import CommandExecutor
from atomic_red_team_mcp.services.indexer import AtomicIndex, create_index


@pytest.fixture
def sample_atomics():
    """Create sample atomic tests for testing."""
    return [
        MetaAtomic(
            name="Test PowerShell 1",
            description="Test 1",
            supported_platforms=["windows"],
            executor=CommandExecutor(name="powershell", command="Get-Process"),
            technique_id="T1059.001",
            technique_name="PowerShell",
            auto_generated_guid=uuid.UUID("a8c41029-8d2a-4661-ab83-e5104c1cb667"),
        ),
        MetaAtomic(
            name="Test PowerShell 2",
            description="Test 2",
            supported_platforms=["windows"],
            executor=CommandExecutor(name="powershell", command="Get-Service"),
            technique_id="T1059.001",
            technique_name="PowerShell",
            auto_generated_guid=uuid.UUID("b9c41029-8d2a-4661-ab83-e5104c1cb668"),
        ),
        MetaAtomic(
            name="Test Bash 1",
            description="Test 3",
            supported_platforms=["linux", "macos"],
            executor=CommandExecutor(name="bash", command="ls"),
            technique_id="T1059.004",
            technique_name="Unix Shell",
            auto_generated_guid=uuid.UUID("c0c41029-8d2a-4661-ab83-e5104c1cb669"),
        ),
    ]


def test_index_initialization(sample_atomics):
    """Test that index initializes correctly."""
    index = AtomicIndex(sample_atomics)

    assert index is not None
    assert len(index.atomics) == 3


def test_index_by_technique_id(sample_atomics):
    """Test lookup by technique ID."""
    index = AtomicIndex(sample_atomics)

    results = index.get_by_technique_id("T1059.001")

    assert len(results) == 2
    assert all(a.technique_id == "T1059.001" for a in results)


def test_index_by_guid(sample_atomics):
    """Test lookup by GUID."""
    index = AtomicIndex(sample_atomics)

    result = index.get_by_guid("a8c41029-8d2a-4661-ab83-e5104c1cb667")

    assert result is not None
    assert result.name == "Test PowerShell 1"


def test_index_by_guid_not_found(sample_atomics):
    """Test lookup by non-existent GUID."""
    index = AtomicIndex(sample_atomics)

    result = index.get_by_guid("nonexistent-guid")

    assert result is None


def test_index_by_platform(sample_atomics):
    """Test lookup by platform."""
    index = AtomicIndex(sample_atomics)

    results = index.get_by_platform("windows")

    assert len(results) == 2
    assert all("windows" in a.supported_platforms for a in results)


def test_index_by_platform_partial_match(sample_atomics):
    """Test partial platform matching."""
    index = AtomicIndex(sample_atomics)

    # Should match both linux and macos
    results = index.get_by_platform("linux")

    assert len(results) >= 1


def test_index_get_techniques(sample_atomics):
    """Test getting all technique IDs."""
    index = AtomicIndex(sample_atomics)

    techniques = index.get_techniques()

    assert "T1059.001" in techniques
    assert "T1059.004" in techniques
    assert len(techniques) == 2


def test_index_get_platforms(sample_atomics):
    """Test getting all platforms."""
    index = AtomicIndex(sample_atomics)

    platforms = index.get_platforms()

    assert "windows" in platforms
    assert "linux" in platforms
    assert "macos" in platforms


def test_index_stats(sample_atomics):
    """Test index statistics."""
    index = AtomicIndex(sample_atomics)

    stats = index.stats()

    assert stats["total_atomics"] == 3
    assert stats["techniques_indexed"] == 2
    assert stats["guids_indexed"] == 3
    assert stats["platforms_indexed"] == 3


def test_create_index_function(sample_atomics):
    """Test that create_index function works correctly."""
    index = create_index(sample_atomics)

    # Should create a valid index
    assert index is not None
    assert len(index.atomics) == len(sample_atomics)


def test_index_empty_list():
    """Test index with empty atomic list."""
    index = AtomicIndex([])

    assert len(index.atomics) == 0
    assert len(index.get_techniques()) == 0
    assert len(index.get_platforms()) == 0


def test_index_performance():
    """Test that indexing provides performance benefits."""
    import time

    # Create a larger dataset
    large_dataset = []
    for i in range(100):
        large_dataset.append(
            MetaAtomic(
                name=f"Test {i}",
                description=f"Test {i}",
                supported_platforms=["windows"],
                executor=CommandExecutor(name="powershell", command="Get-Process"),
                technique_id=f"T1059.{i:03d}",
                technique_name=f"Technique {i}",
                auto_generated_guid=uuid.uuid4(),
            )
        )

    # Measure index creation time
    start = time.time()
    index = AtomicIndex(large_dataset)
    index_time = time.time() - start

    # Measure lookup time
    start = time.time()
    result = index.get_by_technique_id("T1059.050")
    lookup_time = time.time() - start

    # Index creation should be fast (< 100ms for 100 items)
    assert index_time < 0.1

    # Lookup should be very fast (< 10ms)
    assert lookup_time < 0.01

    # Should find the correct item
    assert len(result) == 1
    assert result[0].technique_id == "T1059.050"
