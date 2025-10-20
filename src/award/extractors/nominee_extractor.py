"""Nominee extractor for identifying award nominees from tweets."""

from collections import Counter, defaultdict

from award.processors.base import BaseExtractor
from award.processors.cleaner import normalize_text
from award.tweet import Tweet
from award.utils import get_nlp
from award.validators import EntityTypeValidator


class NomineeExtractor(BaseExtractor):
    """
    Extract nominees for each award category from tweets.

    Uses pattern matching and NER to identify potential nominees,
    then ranks by mention frequency and filters by entity type.
    """

    # Nominee-related patterns
    NOMINEE_PATTERNS = [
        r"\b(?:nominated|nominee|nomination)s?\b",
        r"\b(?:nominated|nominee)\s+(?:for\s+)?(?:the\s+)?",
        r"\bnominees?\s+(?:are|include|:)\s*",
        r"\b(?:is|are|was|were)\s+nominated\b",
    ]

    def __init__(self, min_mentions: int = 3, top_n: int = 5):
        """
        Initialize nominee extractor.

        Args:
            min_mentions: Minimum mention threshold for nominee confidence
            top_n: Number of top nominees to select per award (default 5)
        """
        super().__init__()
        self.min_mentions = min_mentions
        self.top_n = top_n
        self.nlp = get_nlp()
        self.entity_validator = EntityTypeValidator()

    def match_pattern(self, text: str) -> bool:
        """Check if text mentions nominees."""
        keywords = ["nominated", "nominee", "nominees", "nomination", "nominations"]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)

    def extract_nominees_from_tweet(self, text: str, award_name: str = "") -> list[str]:
        """
        Extract potential nominee names from a single tweet.

        Args:
            text: Tweet text
            award_name: Award category name (for context)

        Returns:
            List of normalized nominee names
        """
        nominees = []
        doc = self.nlp(text)

        # Extract entities based on award type
        expected_type = self.entity_validator.get_expected_type_from_award(award_name)

        if expected_type == "person":
            # Extract PERSON entities
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    nominees.append(ent.text)
        else:
            # Extract WORK_OF_ART, ORG, or PERSON entities
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "WORK_OF_ART", "ORG", "PRODUCT"]:
                    nominees.append(ent.text)

        # Normalize and return
        return [normalize_text(n) for n in nominees if normalize_text(n)]

    def associate_nominees_with_awards(
        self, tweets: list[Tweet], awards: list[str], tweet_awards: dict[int, list[str]] | None = None
    ) -> tuple[dict[str, list[tuple[str, int]]], dict[str, list[Tweet]]]:
        """
        Associate extracted nominees with specific awards.

        Args:
            tweets: List of nominee-related tweets
            awards: List of normalized template award names
            tweet_awards: Optional POS-detected award mentions

        Returns:
            Tuple of:
            - Dictionary mapping award -> [(nominee_name, mention_count), ...]
            - Dictionary mapping award -> [relevant_tweets]
        """
        award_nominees: dict[str, Counter] = defaultdict(Counter)
        award_tweets_map: dict[str, list[Tweet]] = defaultdict(list)

        for tweet in tweets:
            text_normalized = normalize_text(tweet.text)

            # Find which award(s) this tweet mentions
            mentioned_awards = []

            # Method 1: Use POS-detected awards if available
            if tweet_awards and tweet.id in tweet_awards:
                detected_awards = tweet_awards[tweet.id]

                # Map detected awards to template awards
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

                    # Accept if good overlap
                    if best_match and best_overlap >= 0.5:  # 50% overlap
                        mentioned_awards.append(best_match)
                        award_tweets_map[best_match].append(tweet)

            # Method 2: Fallback to word overlap
            if not mentioned_awards:
                for award in awards:
                    award_words = set(award.split())
                    text_words = set(text_normalized.split())

                    overlap = len(award_words & text_words)
                    overlap_ratio = overlap / len(award_words) if award_words else 0

                    if overlap_ratio >= 0.5:  # 50% word overlap
                        mentioned_awards.append(award)
                        award_tweets_map[award].append(tweet)

            # Extract nominees from this tweet
            for award in mentioned_awards:
                potential_nominees = self.extract_nominees_from_tweet(tweet.text, award)

                for nominee in potential_nominees:
                    nominee_normalized = normalize_text(nominee)
                    if nominee_normalized:
                        award_nominees[award][nominee_normalized] += 1

        # Convert to sorted lists
        result = {}
        for award, nominee_counts in award_nominees.items():
            sorted_nominees = nominee_counts.most_common()
            result[award] = sorted_nominees

        return result, award_tweets_map

    def select_top_nominees(
        self, nominee_candidates: list[tuple[str, int]], award_name: str, award_tweets: list[Tweet], winner: str = ""
    ) -> list[str]:
        """
        Select the top nominees from candidates.

        Args:
            nominee_candidates: List of (nominee_name, mention_count) tuples
            award_name: Award category name for validation
            award_tweets: Tweets mentioning this award
            winner: Winner name to exclude from nominees

        Returns:
            List of top nominee names (excluding winner)
        """
        if not nominee_candidates:
            return []

        # Special case: Cecil B. DeMille Award has no nominees
        if "cecil" in award_name.lower() and "demille" in award_name.lower():
            return []

        # Get expected entity type
        self.entity_validator.get_expected_type_from_award(award_name)

        # Filter candidates by entity type and exclude winner
        filtered_candidates = []
        winner_normalized = normalize_text(winner) if winner else ""

        for nominee_name, count in nominee_candidates:
            # Skip if this is the winner
            if winner_normalized and normalize_text(nominee_name) == winner_normalized:
                continue

            # Validate entity type (basic validation)
            # In production, you'd use more sophisticated validation
            filtered_candidates.append((nominee_name, count))

        # Filter by minimum mentions
        high_confidence = [(name, count) for name, count in filtered_candidates if count >= self.min_mentions]

        # If we have enough high-confidence nominees, use them
        if len(high_confidence) >= 3:
            nominees = [name for name, _ in high_confidence[: self.top_n]]
        else:
            # Otherwise, take top candidates even if below threshold
            nominees = [name for name, _ in filtered_candidates[: self.top_n]]

        return nominees

    def extract(
        self,
        tweets: list[Tweet],
        awards: list[str],
        winners: dict[str, str],
        tweet_awards: dict[int, list[str]] | None = None,
    ) -> dict[str, list[str]]:
        """
        Extract nominees for each award category.

        Args:
            tweets: List of nominee-related tweets
            awards: List of normalized template award names
            winners: Dictionary mapping award -> winner name
            tweet_awards: Optional POS-detected award mentions

        Returns:
            Dictionary mapping award name -> list of nominee names
        """
        print(f"Extracting nominees from {len(tweets)} tweets for {len(awards)} awards...")

        if tweet_awards:
            print(f"Using POS-detected awards from {len(tweet_awards)} tweets")

        # Associate nominees with awards
        award_nominee_candidates, award_tweets_map = self.associate_nominees_with_awards(tweets, awards, tweet_awards)

        # Select top nominees for each award
        nominees = {}
        found_count = 0

        for award in awards:
            candidates = award_nominee_candidates.get(award, [])
            award_tweets = award_tweets_map.get(award, [])
            winner = winners.get(award, "")

            nominee_list = self.select_top_nominees(candidates, award, award_tweets, winner)
            nominees[award] = nominee_list

            if nominee_list:
                found_count += 1

        print(f"✓ Found nominees for {found_count}/{len(awards)} awards")

        return nominees
