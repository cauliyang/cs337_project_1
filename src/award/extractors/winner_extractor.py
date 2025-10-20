"""Winner extractor for identifying award winners from tweets."""

import re
from collections import Counter, defaultdict

from award.nlp import get_nlp
from award.processors.base import BaseExtractor
from award.tweet import Tweet
from award.utils import normalize_text
from award.validators import EntityTypeValidator


class WinnerExtractor(BaseExtractor):
    """
    Extract winners for each award category from tweets.

    Uses pattern matching and NER to identify winners,
    then associates them with specific awards.
    """

    # Winner-related patterns
    WINNER_PATTERNS = [
        r"\b([\w\s]+?)\s+(?:wins|won|winning)\s+(?:the\s+)?(?:golden\s+globe\s+for\s+)?(.+)",
        r"\b(?:winner|winners?):\s*([\w\s]+)",
        r"\b([\w\s]+?)\s+(?:takes?|gets?|receives?)\s+(?:the\s+)?(?:award|globe)",
        r"\bcongrats?\s+(?:to\s+)?([\w\s]+)",
        r"\b([\w\s]+?)\s+(?:wins|won)\b",
    ]

    def __init__(self, min_mentions: int = 5):
        """
        Initialize winner extractor.

        Args:
            min_mentions: Minimum mention threshold for winner confidence
        """
        super().__init__()
        self.min_mentions = min_mentions
        self.nlp = get_nlp()
        self.entity_validator = EntityTypeValidator()

    def match_pattern(self, text: str) -> bool:
        """Check if text mentions winners."""
        keywords = ["win", "wins", "won", "winner", "congrats", "congratulations"]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)

    def extract_winners_from_tweet(self, text: str) -> list[str]:
        """
        Extract potential winner names from a single tweet.

        Args:
            text: Tweet text

        Returns:
            List of potential winner names
        """
        winners = []

        # Method 1: Pattern matching
        for pattern_str in self.WINNER_PATTERNS:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = pattern.findall(text)
            for match in matches:
                # Extract the name part (first group usually)
                if isinstance(match, tuple):
                    name = match[0]
                else:
                    name = match

                # Clean and validate
                name = name.strip()
                if name and 3 < len(name) < 50:  # Reasonable name length
                    winners.append(name)

        # Method 2: spaCy NER for PERSON entities near "win" keywords
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Check if near win keywords
                ent_text = ent.text.strip()
                if ent_text and 3 < len(ent_text) < 50:
                    winners.append(ent_text)

        return winners

    def associate_winners_with_awards(
        self, tweets: list[Tweet], awards: list[str], tweet_awards: dict[int, list[str]] | None = None
    ) -> tuple[dict[str, list[tuple[str, int]]], dict[str, list[Tweet]]]:
        """
        Associate extracted winners with specific awards using POS-detected award mentions.

        Args:
            tweets: List of winner-related tweets
            awards: List of normalized template award names (to avoid cascade errors)
            tweet_awards: Optional mapping of tweet_id -> [POS-detected award phrases]

        Returns:
            Tuple of:
            - Dictionary mapping award -> [(winner_name, mention_count), ...]
            - Dictionary mapping award -> [relevant_tweets]
        """
        # For each award, find tweets that mention it and extract winners
        award_winners: dict[str, Counter] = defaultdict(Counter)
        award_tweets_map: dict[str, list[Tweet]] = defaultdict(list)

        for tweet in tweets:
            text_normalized = normalize_text(tweet.text)

            # Find which award(s) this tweet mentions
            mentioned_awards = []

            # Method 1: Use POS-detected award mentions if available
            if tweet_awards and tweet.id in tweet_awards:
                detected_awards = tweet_awards[tweet.id]

                # Map detected awards to template awards (fuzzy matching)
                for detected_award in detected_awards:
                    detected_normalized = normalize_text(detected_award)

                    # Find best matching template award
                    best_match = None
                    best_overlap = 0.0

                    for template_award in awards:
                        detected_words = set(detected_normalized.split())
                        template_words = set(template_award.split())

                        overlap = len(detected_words & template_words)
                        overlap_ratio = overlap / len(template_words) if template_words else 0

                        if overlap_ratio > best_overlap:
                            best_overlap = overlap_ratio
                            best_match = template_award

                    # Accept if good overlap (use template award to avoid cascade errors)
                    if best_match and best_overlap >= 0.5:  # 50% overlap with template
                        mentioned_awards.append(best_match)
                        award_tweets_map[best_match].append(tweet)

            # Method 2: Fallback to word overlap if no POS detection
            if not mentioned_awards:
                for award in awards:
                    award_words = set(award.split())
                    text_words = set(text_normalized.split())

                    overlap = len(award_words & text_words)
                    overlap_ratio = overlap / len(award_words) if award_words else 0

                    # More strict threshold for fallback
                    if overlap_ratio >= 0.5:  # 50% word overlap
                        mentioned_awards.append(award)
                        award_tweets_map[award].append(tweet)

            # Extract winners from this tweet
            potential_winners = self.extract_winners_from_tweet(tweet.text)

            # Associate winners with mentioned awards
            for award in mentioned_awards:
                for winner in potential_winners:
                    winner_normalized = normalize_text(winner)
                    if winner_normalized:
                        award_winners[award][winner_normalized] += 1

        # Convert to sorted lists
        result = {}
        for award, winner_counts in award_winners.items():
            # Get top winners sorted by mention count
            sorted_winners = winner_counts.most_common()
            result[award] = sorted_winners

        return result, award_tweets_map

    def select_top_winner(
        self, winner_candidates: list[tuple[str, int]], award_name: str, award_tweets: list[Tweet]
    ) -> str:
        """
        Select the most likely winner from candidates.

        Args:
            winner_candidates: List of (winner_name, mention_count) tuples
            award_name: Award category name for entity type validation
            award_tweets: Tweets mentioning this award (for context)

        Returns:
            Winner name or empty string if no good candidate
        """
        if not winner_candidates:
            return ""

        # Get expected entity type from award
        expected_type = self.entity_validator.get_expected_type_from_award(award_name)

        # Filter candidates by entity type
        filtered_candidates = []
        for winner_name, count in winner_candidates:
            # Find tweet context for this winner
            tweet_context = ""
            for tweet in award_tweets:
                if normalize_text(winner_name) in normalize_text(tweet.text):
                    tweet_context = tweet.text
                    break

            # Validate entity type
            entity_type = self.entity_validator.classify(winner_name, award_name, tweet_context)

            # Keep if matches expected type or unknown (benefit of doubt)
            if entity_type == expected_type or entity_type == "unknown":
                filtered_candidates.append((winner_name, count))

        # If no candidates after filtering, use original list (fallback)
        if not filtered_candidates:
            filtered_candidates = winner_candidates

        # Get top candidate
        top_winner, top_count = filtered_candidates[0]

        # Require minimum mentions for confidence
        if top_count >= self.min_mentions:
            return top_winner

        # If close to threshold, still return it
        if top_count >= self.min_mentions - 2:
            return top_winner

        return ""

    def extract(  # type: ignore[override]
        self, tweets: list[Tweet], awards: list[str], tweet_awards: dict[int, list[str]] | None = None
    ) -> dict[str, str]:
        """
        Extract winners for each award category using POS-detected award mentions.

        Args:
            tweets: List of winner-related tweets
            awards: List of normalized template award names (to avoid cascade errors)
            tweet_awards: Optional mapping of tweet_id -> [POS-detected award phrases]

        Returns:
            Dictionary mapping award -> winner name
        """
        print(f"Extracting winners from {len(tweets)} tweets for {len(awards)} awards...")

        if tweet_awards:
            print(f"Using POS-detected award mentions from {len(tweet_awards)} tweets")

        # Associate winners with awards using POS-detected mentions
        award_winner_candidates, award_tweets_map = self.associate_winners_with_awards(tweets, awards, tweet_awards)

        # Select top winner for each award
        winners = {}
        found_count = 0

        for award in awards:
            candidates = award_winner_candidates.get(award, [])
            award_tweets = award_tweets_map.get(award, [])
            winner = self.select_top_winner(candidates, award, award_tweets)
            winners[award] = winner
            if winner:
                found_count += 1

        print(f"Found winners for {found_count}/{len(awards)} awards")

        return winners
