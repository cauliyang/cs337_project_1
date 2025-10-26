"""
Aggregation module for selecting the most probable candidates from extraction results.

This module provides various strategies to aggregate multiple candidate names
and select the most likely final answer based on different criteria.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .tweet import Tweet


class AggregationStrategy(Enum):
    """Available aggregation strategies."""

    MOST_FREQUENT = "most_frequent"
    LONGEST = "longest"
    HIGHEST_RETWEET_COUNT = "highest_retweet_count"
    WEIGHTED_SCORE = "weighted_score"
    COMBINED = "combined"


@dataclass
class CandidateScore:
    """Represents a candidate with its score and metadata."""

    name: str
    frequency: int
    total_retweets: int
    avg_retweets: float
    max_retweets: int
    length: int
    tweets: list[Tweet]
    weighted_score: float = 0.0


class AwardAggregator:
    """
    Aggregates extracted award information across multiple tweets and selects
    the most probable candidates using various strategies.
    """

    def __init__(self, strategy: AggregationStrategy = AggregationStrategy.COMBINED):
        self.strategy = strategy
        self.candidates: dict[str, CandidateScore] = {}
        self.tweets: list[Tweet] = []

    def add_tweet_data(self, tweet: Tweet, extracted_items: list[str], item_type: str = "general") -> None:
        """
        Add extracted data from a tweet to the aggregator.

        Args:
            tweet: The tweet object containing metadata
            extracted_items: List of extracted names/items from the tweet
            item_type: Type of extracted items (e.g., "awards", "nominees", "winners")
        """
        self.tweets.append(tweet)

        for item in extracted_items:
            if not item or len(item.strip()) < 2:
                continue

            item = item.strip()

            if item not in self.candidates:
                self.candidates[item] = CandidateScore(
                    name=item,
                    frequency=0,
                    total_retweets=0,
                    avg_retweets=0.0,
                    max_retweets=0,
                    length=len(item),
                    tweets=[],
                    weighted_score=0.0,
                )

            # Update candidate statistics
            candidate = self.candidates[item]
            candidate.frequency += 1
            candidate.total_retweets += tweet.retweeted_count
            candidate.max_retweets = max(candidate.max_retweets, tweet.retweeted_count)
            candidate.tweets.append(tweet)
            candidate.avg_retweets = candidate.total_retweets / candidate.frequency

    def get_top_candidates(self, n: int = 5, min_frequency: int = 1) -> list[CandidateScore]:
        """
        Get the top N candidates based on the selected strategy.

        Args:
            n: Number of top candidates to return
            min_frequency: Minimum frequency threshold for candidates

        Returns:
            List of CandidateScore objects sorted by score (highest first)
        """
        # Filter candidates by minimum frequency
        filtered_candidates = {
            name: candidate for name, candidate in self.candidates.items() if candidate.frequency >= min_frequency
        }

        if not filtered_candidates:
            return []

        # Calculate scores based on strategy
        if self.strategy == AggregationStrategy.MOST_FREQUENT:
            scored_candidates = self._score_by_frequency(filtered_candidates)
        elif self.strategy == AggregationStrategy.LONGEST:
            scored_candidates = self._score_by_length(filtered_candidates)
        elif self.strategy == AggregationStrategy.HIGHEST_RETWEET_COUNT:
            scored_candidates = self._score_by_retweets(filtered_candidates)
        elif self.strategy == AggregationStrategy.WEIGHTED_SCORE:
            scored_candidates = self._score_weighted(filtered_candidates)
        elif self.strategy == AggregationStrategy.COMBINED:
            scored_candidates = self._score_combined(filtered_candidates)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

        # Sort by score and return top N
        sorted_candidates = sorted(scored_candidates.values(), key=lambda x: x.weighted_score, reverse=True)
        return sorted_candidates[:n]

    def get_best_candidate(self, min_frequency: int = 1) -> str | None:
        """
        Get the single best candidate based on the selected strategy.

        Args:
            min_frequency: Minimum frequency threshold for candidates

        Returns:
            The best candidate name, or None if no valid candidates
        """
        top_candidates = self.get_top_candidates(n=1, min_frequency=min_frequency)
        return top_candidates[0].name if top_candidates else None

    def _score_by_frequency(self, candidates: dict[str, CandidateScore]) -> dict[str, CandidateScore]:
        """Score candidates by frequency only."""
        for candidate in candidates.values():
            candidate.weighted_score = candidate.frequency
        return candidates

    def _score_by_length(self, candidates: dict[str, CandidateScore]) -> dict[str, CandidateScore]:
        """Score candidates by length (longer is better)."""
        for candidate in candidates.values():
            candidate.weighted_score = candidate.length
        return candidates

    def _score_by_retweets(self, candidates: dict[str, CandidateScore]) -> dict[str, CandidateScore]:
        """Score candidates by total retweet count."""
        for candidate in candidates.values():
            candidate.weighted_score = candidate.total_retweets
        return candidates

    def _score_weighted(self, candidates: dict[str, CandidateScore]) -> dict[str, CandidateScore]:
        """
        Score candidates using a weighted combination of factors:
        - Frequency (40%)
        - Retweet count (40%)
        - Length (20%)
        """
        # Normalize scores to 0-1 range
        max_freq = max(c.frequency for c in candidates.values()) if candidates else 1
        max_retweets = max(c.total_retweets for c in candidates.values()) if candidates else 1
        max_length = max(c.length for c in candidates.values()) if candidates else 1

        for candidate in candidates.values():
            # Avoid division by zero
            freq_score = candidate.frequency / max_freq if max_freq > 0 else 0
            retweet_score = candidate.total_retweets / max_retweets if max_retweets > 0 else 0
            length_score = candidate.length / max_length if max_length > 0 else 0

            candidate.weighted_score = 0.4 * freq_score + 0.4 * retweet_score + 0.2 * length_score

        return candidates

    def _score_combined(self, candidates: dict[str, CandidateScore]) -> dict[str, CandidateScore]:
        """
        Score candidates using a comprehensive combination of factors:
        - Frequency (30%)
        - Retweet count (30%)
        - Average retweets per mention (20%)
        - Length (10%)
        - Maximum retweets (10%)
        """
        # Normalize scores to 0-1 range
        max_freq = max(c.frequency for c in candidates.values()) if candidates else 1
        max_retweets = max(c.total_retweets for c in candidates.values()) if candidates else 1
        max_avg_retweets = max(c.avg_retweets for c in candidates.values()) if candidates else 1
        max_length = max(c.length for c in candidates.values()) if candidates else 1
        max_max_retweets = max(c.max_retweets for c in candidates.values()) if candidates else 1

        for candidate in candidates.values():
            # Avoid division by zero
            freq_score = candidate.frequency / max_freq if max_freq > 0 else 0
            retweet_score = candidate.total_retweets / max_retweets if max_retweets > 0 else 0
            avg_retweet_score = candidate.avg_retweets / max_avg_retweets if max_avg_retweets > 0 else 0
            length_score = candidate.length / max_length if max_length > 0 else 0
            max_retweet_score = candidate.max_retweets / max_max_retweets if max_max_retweets > 0 else 0

            candidate.weighted_score = (
                0.3 * freq_score
                + 0.3 * retweet_score
                + 0.2 * avg_retweet_score
                + 0.1 * length_score
                + 0.1 * max_retweet_score
            )

        return candidates

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the aggregation process."""
        if not self.candidates:
            return {"total_candidates": 0, "total_tweets": 0, "total_retweets": 0, "avg_candidates_per_tweet": 0}

        total_retweets = sum(tweet.retweeted_count for tweet in self.tweets)
        avg_candidates_per_tweet = len(self.candidates) / len(self.tweets) if self.tweets else 0

        return {
            "total_candidates": len(self.candidates),
            "total_tweets": len(self.tweets),
            "total_retweets": total_retweets,
            "avg_candidates_per_tweet": avg_candidates_per_tweet,
            "top_candidate": self.get_best_candidate(),
            "candidate_frequencies": {name: candidate.frequency for name, candidate in self.candidates.items()},
        }

    def clear(self) -> None:
        """Clear all aggregated data."""
        self.candidates.clear()
        self.tweets.clear()


class MultiTypeAggregator:
    """
    Aggregator that handles multiple types of extracted information
    (awards, nominees, winners, presenters, hosts) simultaneously.
    """

    def __init__(self, strategy: AggregationStrategy = AggregationStrategy.COMBINED):
        self.strategy = strategy
        self.aggregators = {
            "awards": AwardAggregator(strategy),
            "nominees": AwardAggregator(strategy),
            "winners": AwardAggregator(strategy),
            "presenters": AwardAggregator(strategy),
            "hosts": AwardAggregator(strategy),
        }

    def add_tweet_data(self, tweet: Tweet, extracted_data: dict[str, list[str]]) -> None:
        """
        Add extracted data from a tweet to the appropriate aggregators.

        Args:
            tweet: The tweet object
            extracted_data: Dictionary mapping item types to lists of extracted items
                          e.g., {"awards": ["Best Actor"], "nominees": ["Daniel Day-Lewis"]}
        """
        for item_type, items in extracted_data.items():
            if item_type in self.aggregators:
                self.aggregators[item_type].add_tweet_data(tweet, items, item_type)

    def get_results(self, min_frequency: int = 1) -> dict[str, list[str]]:
        """
        Get the best candidates for each type.

        Args:
            min_frequency: Minimum frequency threshold for candidates

        Returns:
            Dictionary mapping item types to lists of best candidates
        """
        results = {}
        for item_type, aggregator in self.aggregators.items():
            top_candidates = aggregator.get_top_candidates(n=10, min_frequency=min_frequency)
            results[item_type] = [candidate.name for candidate in top_candidates]

        return results

    def get_single_results(self, min_frequency: int = 1) -> dict[str, str | None]:
        """
        Get the single best candidate for each type.

        Args:
            min_frequency: Minimum frequency threshold for candidates

        Returns:
            Dictionary mapping item types to their best candidate (or None)
        """
        results = {}
        for item_type, aggregator in self.aggregators.items():
            results[item_type] = aggregator.get_best_candidate(min_frequency=min_frequency)

        return results

    def get_statistics(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all aggregators."""
        return {item_type: aggregator.get_statistics() for item_type, aggregator in self.aggregators.items()}
