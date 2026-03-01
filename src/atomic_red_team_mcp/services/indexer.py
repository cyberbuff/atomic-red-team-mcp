"""Performance optimizations for atomic test queries."""

import logging
from collections import defaultdict
from typing import Dict, List, Set

from atomic_red_team_mcp.models import MetaAtomic

logger = logging.getLogger(__name__)


class AtomicIndex:
    """Index atomic tests for fast lookups.

    Provides O(1) lookups for common query patterns:
    - By technique_id
    - By GUID
    - By platform
    """

    def __init__(self, atomics: List[MetaAtomic]):
        """Initialize indexes from atomic tests.

        Args:
            atomics: List of atomic tests to index
        """
        self.atomics = atomics
        self._technique_index: Dict[str, List[MetaAtomic]] = defaultdict(list)
        self._guid_index: Dict[str, MetaAtomic] = {}
        self._platform_index: Dict[str, List[MetaAtomic]] = defaultdict(list)
        self._build_indexes()

    def _build_indexes(self):
        """Build all indexes from atomic tests."""
        logger.debug(f"Building indexes for {len(self.atomics)} atomic tests")

        for atomic in self.atomics:
            # Index by technique_id
            if atomic.technique_id:
                self._technique_index[atomic.technique_id].append(atomic)

            # Index by GUID
            if atomic.auto_generated_guid:
                guid_str = str(atomic.auto_generated_guid)
                self._guid_index[guid_str] = atomic

            # Index by platform
            for platform in atomic.supported_platforms:
                self._platform_index[platform.lower()].append(atomic)

        logger.debug(
            f"Indexes built: {len(self._technique_index)} techniques, "
            f"{len(self._guid_index)} GUIDs, "
            f"{len(self._platform_index)} platforms"
        )

    def get_by_technique_id(self, technique_id: str) -> List[MetaAtomic]:
        """Get all atomic tests for a technique ID.

        Args:
            technique_id: MITRE ATT&CK technique ID (e.g., T1059.001)

        Returns:
            List of atomic tests for the technique (empty if none found)
        """
        return self._technique_index.get(technique_id, [])

    def get_by_guid(self, guid: str) -> MetaAtomic | None:
        """Get atomic test by GUID.

        Args:
            guid: Atomic test GUID (UUID string)

        Returns:
            Atomic test if found, None otherwise
        """
        return self._guid_index.get(guid)

    def get_by_platform(self, platform: str) -> List[MetaAtomic]:
        """Get all atomic tests for a platform.

        Args:
            platform: Platform name (case-insensitive, partial match supported)

        Returns:
            List of atomic tests supporting the platform
        """
        platform_lower = platform.lower()

        # Exact match first
        if platform_lower in self._platform_index:
            return list(self._platform_index[platform_lower])

        # Partial match fallback - deduplicate by GUID to avoid returning
        # the same atomic multiple times when it matches several indexed keys
        results: List[MetaAtomic] = []
        seen_guids: Set[str] = set()
        for indexed_platform, atomics in self._platform_index.items():
            if platform_lower in indexed_platform:
                for atomic in atomics:
                    guid_str = str(atomic.auto_generated_guid)
                    if guid_str not in seen_guids:
                        seen_guids.add(guid_str)
                        results.append(atomic)

        return results

    def get_techniques(self) -> Set[str]:
        """Get all technique IDs in the index.

        Returns:
            Set of technique ID strings
        """
        return set(self._technique_index.keys())

    def get_platforms(self) -> Set[str]:
        """Get all platforms in the index.

        Returns:
            Set of platform strings
        """
        return set(self._platform_index.keys())

    def stats(self) -> Dict[str, int]:
        """Get index statistics.

        Returns:
            Dictionary with index statistics
        """
        return {
            "total_atomics": len(self.atomics),
            "techniques_indexed": len(self._technique_index),
            "guids_indexed": len(self._guid_index),
            "platforms_indexed": len(self._platform_index),
        }


def create_index(atomics: List[MetaAtomic]) -> AtomicIndex:
    """Create an atomic index.

    Args:
        atomics: List of atomic tests

    Returns:
        AtomicIndex instance
    """
    return AtomicIndex(atomics)
