"""Host extractor for identifying ceremony hosts from tweets."""

import re
from collections import Counter

from award.processors.base import BaseExtractor
from award.processors.cleaner import normalize_text
from award.tweet import Tweet
from award.utils import extract_persons, get_nlp


class HostExtractor(BaseExtractor):
    """
    Extract ceremony hosts from tweets.

    Uses pattern matching to identify host-related tweets, then
    extracts PERSON entities and ranks by mention frequency.
    """

    # Host-related patterns
    HOST_PATTERNS = [
        r"\bhost(?:s|ing|ed)?\b",
        r"\bemcee\b",
        r"\bhosting\b",
        r"\bhosted\s+by\b",
    ]

    def __init__(self, min_mentions: int = 100, top_n: int = 2):
        """
        Initialize host extractor.

        Args:
            min_mentions: Minimum mention count threshold for hosts
            top_n: Number of top hosts to return (typically 2)
        """
        super().__init__()
        self.patterns = self.HOST_PATTERNS
        self.min_mentions = min_mentions
        self.top_n = top_n
        self.nlp = get_nlp()

    def match_pattern(self, text: str) -> bool:
        """
        Check if text matches host patterns.

        Args:
            text: Tweet text to check

        Returns:
            True if text mentions hosting, False otherwise
        """
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in self.patterns)

    def extract(self, tweets: list[Tweet]) -> list[str]:
        """
        Extract hosts from a list of tweets.

        Args:
            tweets: List of Tweet objects to process

        Returns:
            List of normalized host names (typically 2 hosts)
        """
        print("Extracting hosts...")

        # Step 1: Filter tweets mentioning hosts
        host_tweets = [tweet for tweet in tweets if self.match_pattern(tweet.text)]
        print(f"Found {len(host_tweets)} host-related tweets")

        # Step 2: Extract PERSON entities from host tweets
        person_mentions = []
        for tweet in host_tweets:
            persons = extract_persons(tweet.text, self.nlp)
            # Normalize each person name
            normalized_persons = [normalize_text(p) for p in persons if p]
            person_mentions.extend(normalized_persons)

        # Step 3: Count mentions
        person_counts = Counter(person_mentions)
        print(f"Found {len(person_counts)} unique persons mentioned")

        # Step 4: Select top N hosts with sufficient mentions
        hosts = self.select_top_n(person_counts, self.top_n, self.min_mentions)

        print(f"Selected hosts: {hosts}")
        return hosts
