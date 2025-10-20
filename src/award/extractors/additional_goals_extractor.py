"""Additional goals extractor for fun categories like Best Dressed, Worst Dressed, etc."""

import re
from collections import Counter

from award.processors.base import BaseExtractor
from award.processors.cleaner import normalize_text
from award.tweet import Tweet
from award.utils import get_nlp


class AdditionalGoalsExtractor(BaseExtractor):
    """
    Extract additional goals (fun categories) from tweets.

    Categories:
    - Best Dressed
    - Worst Dressed
    - Best Speech/Moment
    - Most Talked About

    Only extracts winners (most mentioned), no nominees or presenters.
    """

    # Pattern definitions for each category
    BEST_DRESSED_PATTERNS = [
        re.compile(r"\bbest\s+dressed\b", re.IGNORECASE),
        re.compile(r"\blooks?\s+(?:amazing|stunning|gorgeous|beautiful|fabulous)\b", re.IGNORECASE),
        re.compile(r"\b(?:love|loved)\s+(?:her|his|their)\s+(?:dress|gown|outfit|look)\b", re.IGNORECASE),
    ]

    WORST_DRESSED_PATTERNS = [
        re.compile(r"\bworst\s+dressed\b", re.IGNORECASE),
        re.compile(r"\bterrible\s+(?:dress|gown|outfit|look)\b", re.IGNORECASE),
        re.compile(r"\bwhat\s+was\s+(?:she|he)\s+wearing\b", re.IGNORECASE),
        re.compile(r"\bfashion\s+(?:disaster|fail)\b", re.IGNORECASE),
    ]

    SPEECH_PATTERNS = [
        re.compile(r"\bspeech\b", re.IGNORECASE),
        re.compile(r"\bacceptance\s+speech\b", re.IGNORECASE),
        re.compile(r"\bthank\s+you\s+speech\b"),
        re.compile(r"\bspoke\b", re.IGNORECASE),
    ]

    POSITIVE_SPEECH = [
        re.compile(r"\bbest\s+speech\b", re.IGNORECASE),
        re.compile(r"\b(?:amazing|great|incredible|moving|touching)\s+speech\b", re.IGNORECASE),
        re.compile(r"\bloved\s+(?:her|his|their)\s+speech\b", re.IGNORECASE),
    ]

    NEGATIVE_SPEECH = [
        re.compile(r"\bworst\s+speech\b", re.IGNORECASE),
        re.compile(r"\b(?:awkward|rambling|long|boring)\s+speech\b", re.IGNORECASE),
    ]

    def __init__(self, min_mentions: int = 5):
        """
        Initialize additional goals extractor.

        Args:
            min_mentions: Minimum mention threshold for confidence
        """
        super().__init__()
        self.min_mentions = min_mentions
        self.nlp = get_nlp()

    def match_pattern(self, text: str) -> bool:
        """Check if text matches any additional goal patterns."""
        # Combine all patterns for general matching
        all_patterns = (
            self.BEST_DRESSED_PATTERNS
            + self.WORST_DRESSED_PATTERNS
            + self.SPEECH_PATTERNS
            + self.POSITIVE_SPEECH
            + self.NEGATIVE_SPEECH
        )
        return self.match_patterns(text, all_patterns)

    def extract_persons_from_tweet(self, text: str) -> list[str]:
        """Extract PERSON entities from tweet."""
        doc = self.nlp(text)
        persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        return [normalize_text(p) for p in persons if normalize_text(p)]

    def match_patterns(self, text: str, patterns: list[str]) -> bool:
        """Check if text matches any pattern in the list."""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in patterns)

    def extract_best_dressed(self, tweets: list[Tweet]) -> str:
        """Extract best dressed person."""
        person_counts: Counter[str] = Counter()

        for tweet in tweets:
            if self.match_patterns(tweet.text, self.BEST_DRESSED_PATTERNS):
                persons = self.extract_persons_from_tweet(tweet.text)
                person_counts.update(persons)

        # Get top person
        if person_counts:
            most_common = person_counts.most_common(1)
            if most_common and most_common[0][1] >= self.min_mentions:
                return most_common[0][0]

        return ""

    def extract_worst_dressed(self, tweets: list[Tweet]) -> str:
        """Extract worst dressed person."""
        person_counts: Counter[str] = Counter()

        for tweet in tweets:
            if self.match_patterns(tweet.text, self.WORST_DRESSED_PATTERNS):
                persons = self.extract_persons_from_tweet(tweet.text)
                person_counts.update(persons)

        # Get top person
        if person_counts:
            most_common = person_counts.most_common(1)
            if most_common and most_common[0][1] >= self.min_mentions:
                return most_common[0][0]

        return ""

    def extract_best_speech(self, tweets: list[Tweet]) -> str:
        """Extract person with best speech."""
        person_counts: Counter[str] = Counter()

        for tweet in tweets:
            # Check for positive speech mentions
            if self.match_patterns(tweet.text, self.POSITIVE_SPEECH):
                persons = self.extract_persons_from_tweet(tweet.text)
                person_counts.update(persons)

        # Get top person
        if person_counts:
            most_common = person_counts.most_common(1)
            if most_common and most_common[0][1] >= self.min_mentions:
                return most_common[0][0]

        return ""

    def extract_most_talked_about(self, tweets: list[Tweet]) -> str:
        """Extract most talked about person overall."""
        person_counts: Counter[str] = Counter()

        # Count all person mentions across all tweets
        for tweet in tweets:
            persons = self.extract_persons_from_tweet(tweet.text)
            person_counts.update(persons)

        # Get top person, excluding hosts (they're already known)
        if person_counts:
            # Filter out common hosts
            host_names = {"tina fey", "amy poehler", "tina", "amy"}
            filtered_counts = {
                person: count
                for person, count in person_counts.items()
                if person not in host_names and count >= self.min_mentions * 2
            }

            if filtered_counts:
                most_common = max(filtered_counts.items(), key=lambda x: x[1])
                return most_common[0]

        return ""

    def extract(self, tweets: list[Tweet]) -> dict[str, str]:
        """
        Extract all additional goals from tweets.

        Args:
            tweets: List of Tweet objects

        Returns:
            Dictionary mapping goal name to winner
            Example: {
                "Best Dressed": "jennifer lawrence",
                "Worst Dressed": "anne hathaway",
                "Best Speech": "jodie foster",
                "Most Talked About": "ben affleck"
            }
        """
        print(f"Extracting additional goals from {len(tweets)} tweets...")

        results = {}

        # Extract each category
        best_dressed = self.extract_best_dressed(tweets)
        if best_dressed:
            results["Best Dressed"] = best_dressed
            print(f"  Best Dressed: {best_dressed}")

        worst_dressed = self.extract_worst_dressed(tweets)
        if worst_dressed:
            results["Worst Dressed"] = worst_dressed
            print(f"  Worst Dressed: {worst_dressed}")

        best_speech = self.extract_best_speech(tweets)
        if best_speech:
            results["Best Speech"] = best_speech
            print(f"  Best Speech: {best_speech}")

        most_talked = self.extract_most_talked_about(tweets)
        if most_talked:
            results["Most Talked About"] = most_talked
            print(f"  Most Talked About: {most_talked}")

        print(f"✓ Extracted {len(results)} additional goals")

        return results
