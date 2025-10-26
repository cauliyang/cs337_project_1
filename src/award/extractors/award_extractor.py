"""Award extractor for discovering award category names from tweets."""

import re
from collections import Counter
from difflib import SequenceMatcher

from nltk import RegexpParser

from award.processors.base import BaseExtractor
from award.processors.cleaner import normalize_text
from award.tweet import Tweet
from award.utils import load_nltk_data


class AwardExtractor(BaseExtractor):
    """
    Extract and discover award category names from tweets.

    Uses pattern matching to dynamically discover awards from tweets,
    then clusters similar phrases into canonical award names.
    """

    # Backup regex pattern (for Cecil B. DeMille and validation)
    CECIL_PATTERN = re.compile(r"\bcecil\s+b\.?\s+demille\s+award\b", re.IGNORECASE)

    # POS-based grammar for award extraction
    # Pattern: Best (RBS/JJS) + optional adjectives/nouns + prepositions + more modifiers
    # Examples:
    # - "Best (RBS) Supporting (JJ) Actress (NN)"
    # - "Best (RBS) Motion (NN) Picture (NN) - Drama"
    # - "Best (RBS) Performance (NN) by (IN) an Actor (NN) in (IN) a Motion Picture (NN)"
    AWARD_GRAMMAR = r"""
        AWARD: {<RBS|JJS><VBG>?<JJ.*>*<NN.*>+<IN>?<DT>?<JJ.*>*<NN.*>*<IN>?<DT>?<JJ.*>*<NN.*>*}
    """

    def __init__(self, min_mentions: int = 5, cluster_threshold: float = 0.8, expected_count: int = 26):
        """
        Initialize award extractor.

        Args:
            min_mentions: Minimum mention count for an award phrase
            cluster_threshold: Similarity threshold for clustering similar awards
            expected_count: Expected number of awards (~26 for Golden Globes)
        """
        super().__init__()
        self.min_mentions = min_mentions
        self.cluster_threshold = cluster_threshold
        self.expected_count = expected_count

        load_nltk_data()

        # Initialize NLTK chunk parser with award grammar
        self.chunk_parser = RegexpParser(self.AWARD_GRAMMAR)

    def match_pattern(self, text: str) -> bool:
        """Check if text mentions awards."""
        return "best" in text.lower() or "cecil" in text.lower()

    def extract_award_phrases(self, text: str) -> list[str]:
        """
        Extract award phrases from tweet text using regex patterns (fast) with POS validation (accurate).

        Args:
            text: Tweet text

        Returns:
            List of normalized award phrases
        """
        phrases = []

        # Special case: Cecil B. DeMille Award
        if self.CECIL_PATTERN.search(text):
            phrases.append("cecil b demille award")

        # Fast regex-based extraction for "best X" patterns
        # Pattern captures: best + words + end keywords (actor/picture/film/etc)
        pattern = re.compile(
            r"\bbest\s+[\w\s\-,]+?(?:actor|actress|picture|film|director|score|song|screenplay|series|feature|television|performance)",
            re.IGNORECASE,
        )

        matches = pattern.findall(text)
        for match in matches:
            normalized = normalize_text(match)
            if normalized and 10 < len(normalized) < 100:
                phrases.append(normalized)

        return phrases

    def cluster_similar_awards(self, award_counts: Counter) -> dict[str, list[str]]:
        """
        Cluster similar award phrases together.

        Args:
            award_counts: Counter of award phrases with mention counts

        Returns:
            Dictionary mapping canonical phrase -> list of similar phrases
        """
        clusters = {}
        processed = set()

        # Sort by frequency (most common becomes canonical)
        sorted_phrases = [phrase for phrase, _ in award_counts.most_common()]

        for phrase in sorted_phrases:
            if phrase in processed:
                continue

            # Start new cluster
            cluster = [phrase]
            processed.add(phrase)

            # Find similar phrases
            for other_phrase in sorted_phrases:
                if other_phrase in processed:
                    continue

                # Calculate similarity
                similarity = SequenceMatcher(None, phrase, other_phrase).ratio()

                if similarity >= self.cluster_threshold:
                    cluster.append(other_phrase)
                    processed.add(other_phrase)

            # Use longest phrase as canonical (most complete)
            canonical = max(cluster, key=len)
            clusters[canonical] = cluster

        return clusters

    def canonicalize_award_name(self, award: str) -> str:
        """
        Canonicalize award name for consistency and quality.

        Args:
            award: Award phrase

        Returns:
            Canonicalized award name
        """
        # Normalize spacing
        award = " ".join(award.split())

        # Remove junk at the end (URLs, punctuation fragments)
        award = re.sub(r"\s+http.*$", "", award)
        award = re.sub(r'\s+[\'"\(].*$', "", award)  # Remove dangling quotes/parens
        award = re.sub(
            r"\s+(for|at|winner|wins?|won|goes?\s+to).*$", "", award
        )  # Remove "for argo", "at golden globes", etc.

        # Normalize spacing again after removals
        award = " ".join(award.split())

        # Special case: Cecil B. DeMille Award (restore periods)
        if "cecil" in award and "demille" in award:
            return "cecil b. demille award"

        # Standardize common variations (order matters!)
        replacements = [
            (" award", ""),  # Remove redundant "award"
            (" globe", ""),  # Remove redundant "globe"
            ("made for tv", "made for television"),
            ("tv series", "television series"),
            ("miniseries", "mini-series"),
            ("mini series", "mini-series"),
            (" - ", " "),  # Remove dashes between words initially
        ]

        for old, new in replacements:
            award = award.replace(old, new)

        # Be careful with "tv" -> "television" to not double-replace
        if "television" not in award:
            award = award.replace("tv", "television")

        # Normalize spacing after replacements
        award = " ".join(award.split())

        # Add back specific dashes for consistency
        # "best motion picture drama" -> "best motion picture - drama"
        if "motion picture" in award and ("drama" in award or "comedy" in award or "musical" in award):
            if " drama" in award and "motion picture - drama" not in award:
                award = award.replace(" drama", " - drama")
            if " comedy" in award and "motion picture - comedy" not in award:
                award = award.replace(" comedy", " - comedy or musical")
            if " musical" in award and "motion picture - comedy or musical" not in award:
                award = award.replace(" musical", " - comedy or musical")

        # "best television series drama" -> "best television series - drama"
        if "television series" in award and ("drama" in award or "comedy" in award or "musical" in award):
            if " drama" in award and "television series - drama" not in award:
                award = award.replace(" drama", " - drama")
            if " comedy" in award and "television series - comedy" not in award:
                award = award.replace(" comedy", " - comedy or musical")
            if " musical" in award and "television series - comedy or musical" not in award:
                award = award.replace(" musical", " - comedy or musical")

        # Handle specific award types
        if "director" in award and "motion picture" in award:
            award = "best director - motion picture"
        if "screenplay" in award and "motion picture" in award:
            award = "best screenplay - motion picture"
        if "original score" in award and "motion picture" in award:
            award = "best original score - motion picture"
        if "original song" in award and "motion picture" in award:
            award = "best original song - motion picture"

        # Handle performance awards (normalize to full names)
        if "actress" in award or "actor" in award:
            if "supporting" in award:
                if "motion picture" in award:
                    award_type = "actress" if "actress" in award else "actor"
                    award = f"best performance by an {award_type} in a supporting role in a motion picture"
                elif "television" in award or "series" in award:
                    award_type = "actress" if "actress" in award else "actor"
                    award = f"best performance by an {award_type} in a supporting role in a series, mini-series or motion picture made for television"  # noqa: E501
            elif "mini-series" in award or "television" in award:
                if "drama" in award:
                    award_type = "actress" if "actress" in award else "actor"
                    award = f"best performance by an {award_type} in a television series - drama"
                elif "comedy" in award or "musical" in award:
                    award_type = "actress" if "actress" in award else "actor"
                    award = f"best performance by an {award_type} in a television series - comedy or musical"

        return award.strip()

    def extract(self, tweets: list[Tweet], tweet_awards: dict[int, list[str]] | None = None) -> list[str]:
        """
        Extract award categories from tweets through discovery and clustering.

        Args:
            tweets: List of Tweet objects
            tweet_awards: Optional pre-extracted award mentions from POS tagging (tweet_id -> [awards])

        Returns:
            List of normalized, canonicalized award names
        """
        print("Extracting awards...")

        # Step 1: Extract all award phrases from tweets
        phrase_counts = Counter()

        if tweet_awards:
            # Use pre-extracted POS-detected award mentions
            print(f"Using POS-detected awards from {len(tweet_awards)} tweets")
            for _tweet_id, awards in tweet_awards.items():
                phrase_counts.update(awards)
        else:
            # Fallback: extract from tweets directly
            print("Extracting awards from tweet text (fallback)")
            for tweet in tweets:
                if self.match_pattern(tweet.text):
                    phrases = self.extract_award_phrases(tweet.text)
                    phrase_counts.update(phrases)

        print(f"Found {len(phrase_counts)} unique award phrases")

        # Step 2: Filter by minimum mentions
        filtered_counts = Counter(
            {phrase: count for phrase, count in phrase_counts.items() if count >= self.min_mentions}
        )
        print(f"After filtering: {len(filtered_counts)} phrases with >={self.min_mentions} mentions")

        # Step 3: Cluster similar award phrases
        clusters = self.cluster_similar_awards(filtered_counts)
        print(f"Clustered into {len(clusters)} award categories")

        # Step 4: Canonicalize award names and deduplicate
        canonicalized_awards = {}  # award_name -> total_mentions
        for canonical_phrase, cluster_members in clusters.items():
            # Get total mentions across all cluster members
            total_mentions = sum(filtered_counts[phrase] for phrase in cluster_members)

            # Canonicalize the name
            canonicalized = self.canonicalize_award_name(canonical_phrase)

            # Skip if too short (e.g., just "best")
            if len(canonicalized.split()) < 2:
                continue

            # Merge duplicates (add mentions if already exists)
            if canonicalized in canonicalized_awards:
                canonicalized_awards[canonicalized] += total_mentions
            else:
                canonicalized_awards[canonicalized] = total_mentions

        # Step 5: Sort by mention frequency and select top awards
        sorted_awards = sorted(canonicalized_awards.items(), key=lambda x: x[1], reverse=True)

        # Take top expected_count awards (typically 26)
        final_awards = [award for award, _ in sorted_awards[: self.expected_count]]

        # Validate
        if not (20 <= len(final_awards) <= 30):
            print(f"Warning: Unusual award count: {len(final_awards)} (expected ~{self.expected_count})")

        print(f"Selected {len(final_awards)} unique awards (after deduplication)")
        return final_awards
