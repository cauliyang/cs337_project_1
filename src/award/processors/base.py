"""Base extractor class for entity extraction."""

from abc import ABC, abstractmethod
from collections import Counter
from typing import Any


class BaseExtractor(ABC):
    """
    Abstract base class for extracting entities from tweets.

    All specialized extractors (HostExtractor, AwardExtractor, etc.)
    should extend this class and implement the required methods.
    """

    def __init__(self):
        """Initialize the base extractor."""
        self.patterns: list[str] = []

    @abstractmethod
    def extract(self, tweets: list[Any]) -> Any:
        """
        Extract entities from a list of tweets.

        Args:
            tweets: List of Tweet objects to process

        Returns:
            Extracted entities (format depends on extractor type)
        """
        pass

    @abstractmethod
    def match_pattern(self, text: str) -> bool:
        """
        Check if text matches extraction patterns.

        Args:
            text: Tweet text to check

        Returns:
            True if text matches pattern, False otherwise
        """
        pass

    def count_mentions(self, entities: list[str]) -> Counter:
        """
        Count frequency of entity mentions.

        Args:
            entities: List of entity names

        Returns:
            Counter object with entity mention frequencies
        """
        return Counter(entities)

    def select_top_n(self, entity_counts: Counter, n: int, min_threshold: int = 0) -> list[str]:
        """
        Select top N most-mentioned entities.

        Args:
            entity_counts: Counter with entity frequencies
            n: Number of top entities to return
            min_threshold: Minimum mention count threshold

        Returns:
            List of top N entity names
        """
        # Filter by threshold
        if min_threshold > 0:
            entity_counts = Counter({k: v for k, v in entity_counts.items() if v >= min_threshold})

        # Return top N
        return [entity for entity, count in entity_counts.most_common(n)]
