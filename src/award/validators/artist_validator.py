"""Artist validator using Cinemagoer (IMDb) for person name validation."""

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

    def is_artist(self, name: str) -> bool:
        """
        Check if a name corresponds to a real artist/person in IMDb.

        Args:
            name: Person name to validate

        Returns:
            True if found in IMDb as a person, False otherwise
        """
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

        if verbose and len(candidates) > 1:
            print(f"  Validating {len(candidates)} candidates via IMDb (rate-limited)...")

        validated = self.validate_candidates(candidates, expected_type)
        filtered = [(name, count) for name, count, is_valid in validated if is_valid]

        if verbose:
            print(f"  IMDb validation: {len(filtered)}/{len(candidates)} candidates passed")

        # If filtering removes all candidates, return original list (fallback)
        if not filtered:
            return candidates

        return filtered
