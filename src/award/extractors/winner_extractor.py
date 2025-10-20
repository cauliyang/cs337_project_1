"""Winner extractor for identifying award winners from tweets."""

import re
from collections import Counter, defaultdict

from award.processors.base import BaseExtractor
from award.processors.cleaner import normalize_text
from award.tweet import Tweet
from award.utils import get_nlp
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

    def __init__(self, min_mentions: int = 3):
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

        # Primary method: spaCy NER for clean entity extraction
        # This is more reliable than regex for avoiding fragments
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "WORK_OF_ART", "ORG"]:
                ent_text = ent.text.strip()
                # More lenient length check to capture full names
                if ent_text and 2 < len(ent_text) < 60:
                    winners.append(ent_text)

        # Fallback: Pattern matching only for specific formats
        # Only use the clearest patterns to avoid noise
        specific_patterns = [
            r"\b(?:winner|winners?):\s*([\w\s'-]+?)(?:\s+for|\s+in|\s*$)",  # "Winner: Name"
            r"\bcongrats?\s+(?:to\s+)?([\w\s'-]+?)(?:\s+for|\s+on|\s*$)",  # "Congrats Name"
        ]

        for pattern_str in specific_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = pattern.findall(text)
            for match in matches:
                name = match.strip() if isinstance(match, str) else match[0].strip()
                # Only add if not already captured by NER
                if name and 2 < len(name) < 60 and name not in winners:
                    winners.append(name)

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
                    # STRICTER: 65% overlap to reduce false positives while maintaining recall
                    if best_match and best_overlap >= 0.65:  # 65% overlap with template
                        mentioned_awards.append(best_match)
                        award_tweets_map[best_match].append(tweet)

            # Method 2: Fallback to word overlap if no POS detection
            if not mentioned_awards:
                for award in awards:
                    award_words = set(award.split())
                    text_words = set(text_normalized.split())

                    overlap = len(award_words & text_words)
                    overlap_ratio = overlap / len(award_words) if award_words else 0

                    # STRICTER: 65% word overlap for fallback matching
                    # Reduces false matches while maintaining reasonable recall
                    if overlap_ratio >= 0.65:  # 65% word overlap
                        mentioned_awards.append(award)
                        award_tweets_map[award].append(tweet)

            # Extract winners from this tweet
            potential_winners = self.extract_winners_from_tweet(tweet.text)

            # Associate winners with mentioned awards
            # Weight tweets with strong winner signals more heavily
            text_lower = tweet.text.lower()
            strong_winner_signals = [" wins ", " won ", " winner ", " winning ", "congrats", "congratulations"]
            weight = 2 if any(signal in text_lower for signal in strong_winner_signals) else 1

            for award in mentioned_awards:
                for winner in potential_winners:
                    winner_normalized = normalize_text(winner)
                    if winner_normalized:
                        award_winners[award][winner_normalized] += weight

        # Convert to sorted lists
        result = {}
        for award, winner_counts in award_winners.items():
            # Get top winners sorted by mention count
            sorted_winners = winner_counts.most_common()
            result[award] = sorted_winners

        return result, award_tweets_map

    def select_top_winner(
        self,
        winner_candidates: list[tuple[str, int]],
        award_name: str,
        award_tweets: list[Tweet],
        top_n: int = 1,
    ) -> str:
        """
        Select the most likely winner from candidates by scoring top N.

        Args:
            winner_candidates: List of (winner_name, mention_count) tuples
            award_name: Award category name for entity type validation
            award_tweets: Tweets mentioning this award (for context)
            top_n: Number of top candidates to consider for scoring (default 3)

        Returns:
            Winner name or empty string if no good candidate
        """
        if not winner_candidates:
            return ""

        # Get expected entity type from award
        expected_type = self.entity_validator.get_expected_type_from_award(award_name)

        # Filter out award name fragments (e.g., "best performance", "best actor", "cecil b demille")
        # These are noise from tweets mentioning the award itself
        award_keywords = {"best", "award", "performance", "actor", "actress", "director", "globe", "golden"}
        award_normalized = normalize_text(award_name)
        award_words = set(award_normalized.split())

        # Filter candidates by entity type and quality
        filtered_candidates = []
        for winner_name, count in winner_candidates:
            winner_normalized = normalize_text(winner_name)
            winner_words = set(winner_normalized.split())

            # Skip if it's just award keywords (noise)
            if winner_words and winner_words.issubset(award_keywords):
                continue  # Skip award fragments like "best performance"

            # Skip if winner significantly overlaps with award name (>60% overlap)
            # This catches cases like "cecil b demille" for "cecil b. demille award"
            if winner_words and award_words:
                overlap = len(winner_words & award_words)
                overlap_ratio = overlap / len(winner_words) if winner_words else 0
                if overlap_ratio > 0.6:
                    continue  # Skip award name itself

            # Find tweet context for this winner
            tweet_context = ""
            for tweet in award_tweets:
                if winner_normalized in normalize_text(tweet.text):
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

        # Take top N candidates and score them more carefully
        top_candidates = filtered_candidates[:top_n]

        # Score each candidate based on multiple signals
        scored_candidates = []
        for winner_name, base_count in top_candidates:
            winner_normalized = normalize_text(winner_name)
            score = 0.0

            # Signal 1: Base frequency (heavily weighted - keep top candidate as default)
            max_count = top_candidates[0][1]
            score += (base_count / max_count) * 60  # Up to 60 points (increased from 40)

            # Signal 2: Strong winner context (how many tweets have clear winner signals)
            strong_context_count = 0
            total_mentions = 0
            strong_signals = [" wins ", " won ", " winner is ", " winner:", "congrats", "congratulations"]

            for tweet in award_tweets:
                text_lower = tweet.text.lower()
                if winner_normalized in normalize_text(tweet.text):
                    total_mentions += 1
                    if any(signal in text_lower for signal in strong_signals):
                        strong_context_count += 1

            if total_mentions > 0:
                strong_ratio = strong_context_count / total_mentions
                # Only boost if ratio is significantly high (>50%)
                if strong_ratio > 0.5:
                    score += strong_ratio * 20  # Up to 20 points (reduced from 40)

            # Signal 3: Name completeness (prefer full names over partial)
            word_count = len(winner_normalized.split())
            if word_count >= 2:
                score += 10  # +10 for full names
            elif word_count >= 3:
                score += 5  # +5 bonus for very complete names

            # Signal 4: Entity type confidence
            tweet_context = ""
            for tweet in award_tweets:
                if winner_normalized in normalize_text(tweet.text):
                    tweet_context = tweet.text
                    break

            entity_type = self.entity_validator.classify(winner_name, award_name, tweet_context)
            if entity_type == expected_type:
                score += 10  # +10 for matching entity type

            scored_candidates.append((winner_name, score, base_count))

        # Sort by score (descending)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Get best candidate
        best_winner, best_score, best_count = scored_candidates[0]

        # Clean up the winner name (strip whitespace)
        best_winner = best_winner.strip()

        # Require minimum mentions for confidence
        if best_count >= self.min_mentions:
            return best_winner

        # If close to threshold, still return it
        if best_count >= self.min_mentions - 2:
            return best_winner

        return ""

    def extract(  # type: ignore[override]
        self,
        tweets: list[Tweet],
        awards: list[str],
        tweet_awards: dict[int, list[str]] | None = None,
        hosts: list[str] | None = None,
    ) -> dict[str, str]:
        """
        Extract winners for each award category using POS-detected award mentions.

        Args:
            tweets: List of winner-related tweets
            awards: List of normalized template award names (to avoid cascade errors)
            tweet_awards: Optional mapping of tweet_id -> [POS-detected award phrases]
            hosts: Optional list of hosts to filter out from winner candidates

        Returns:
            Dictionary mapping award -> winner name
        """
        print(f"Extracting winners from {len(tweets)} tweets for {len(awards)} awards...")

        if tweet_awards:
            print(f"Using POS-detected award mentions from {len(tweet_awards)} tweets")

        # Associate winners with awards using POS-detected mentions
        award_winner_candidates, award_tweets_map = self.associate_winners_with_awards(tweets, awards, tweet_awards)

        # Filter out hosts from all candidates
        hosts_normalized = set([normalize_text(h) for h in (hosts or [])])
        if hosts_normalized:
            for award in award_winner_candidates:
                # Remove host names from candidates
                award_winner_candidates[award] = [
                    (name, count) for name, count in award_winner_candidates[award] if name not in hosts_normalized
                ]

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
