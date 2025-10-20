"""Artist validator using Cinemagoer (IMDb) for person name validation."""

import time
from threading import Lock

from imdb import Cinemagoer


class ArtistValidator:
    """
    Validate person names using IMDb/Cinemagoer.

    Uses caching to minimize API calls and improve performance.
    """

    def __init__(self, rate_limit_delay: float = 0.5):
        """
        Initialize Cinemagoer instance with rate limiting.

        Args:
            rate_limit_delay: Minimum seconds between API requests (default 0.5s = 2 req/sec)
        """
        self.ia = Cinemagoer()
        self._cache = {}  # name -> (is_artist, timestamp)
        self._cache_ttl = 3600  # 1 hour cache
        self._rate_limit_delay = rate_limit_delay
        self._last_request_time = 0
        self._request_lock = Lock()

    def is_artist(self, name: str) -> bool:
        """
        Check if a name corresponds to a real artist/person in IMDb.

        Args:
            name: Person name to validate

        Returns:
            True if found in IMDb as a person, False otherwise
        """
        if not name or len(name) < 2:
            return False

        # Clean the name
        name_clean = name.strip().lower()

        # Check cache first
        current_time = time.time()
        if name_clean in self._cache:
            is_artist, timestamp = self._cache[name_clean]
            if current_time - timestamp < self._cache_ttl:
                return is_artist

        try:
            # Rate limiting: ensure minimum delay between requests
            with self._request_lock:
                current_request_time = time.time()
                time_since_last = current_request_time - self._last_request_time

                if time_since_last < self._rate_limit_delay:
                    sleep_time = self._rate_limit_delay - time_since_last
                    time.sleep(sleep_time)

                # Search IMDb for the person
                results = self.ia.search_person(name_clean)
                self._last_request_time = time.time()

            # Check if any result is a good match
            for person in results[:3]:  # Check top 3 results
                person_name = person.get("name", "").lower()

                # Exact match or very close match
                if person_name == name_clean or name_clean in person_name:
                    # Cache positive result
                    self._cache[name_clean] = (True, current_time)
                    return True

            # No match found
            self._cache[name_clean] = (False, current_time)
            return False

        except Exception as e:
            # On error, assume it's an artist (don't filter)
            # Only print first few errors to avoid spam
            if len(self._cache) < 5:
                print(f"Warning: Cinemagoer lookup failed for '{name}': {e}")
            return True

    def validate_candidates(
        self, candidates: list[tuple[str, int]], expected_type: str = "person"
    ) -> list[tuple[str, int, bool]]:
        """
        Validate a list of candidate names against IMDb.

        Args:
            candidates: List of (name, count) tuples
            expected_type: Expected entity type ('person' or other)

        Returns:
            List of (name, count, is_valid_artist) tuples
        """
        if expected_type != "person":
            # Only validate for person awards
            return [(name, count, True) for name, count in candidates]

        validated = []
        for name, count in candidates:
            is_valid = self.is_artist(name)
            validated.append((name, count, is_valid))

        return validated

    def filter_non_artists(
        self, candidates: list[tuple[str, int]], expected_type: str = "person", verbose: bool = False
    ) -> list[tuple[str, int]]:
        """
        Filter out candidates that are not found in IMDb.

        Args:
            candidates: List of (name, count) tuples
            expected_type: Expected entity type
            verbose: Print progress information

        Returns:
            Filtered list of (name, count) tuples
        """
        if expected_type != "person":
            # Don't filter for non-person awards
            return candidates

        if verbose and self.available and len(candidates) > 1:
            print(f"  Validating {len(candidates)} candidates via IMDb (rate-limited)...")

        validated = self.validate_candidates(candidates, expected_type)
        filtered = [(name, count) for name, count, is_valid in validated if is_valid]

        if verbose and self.available:
            print(f"  IMDb validation: {len(filtered)}/{len(candidates)} candidates passed")

        # If filtering removes all candidates, return original list (fallback)
        if not filtered:
            return candidates

        return filtered
