"""Presenter extractor for identifying award presenters from tweets."""

from collections import Counter, defaultdict

from award.processors.base import BaseExtractor
from award.processors.cleaner import normalize_text
from award.tweet import Tweet
from award.utils import get_nlp


class PresenterExtractor(BaseExtractor):
    """
    Extract presenters for each award category from tweets.

    Uses pattern matching and NER to identify presenters,
    focusing on PERSON entities since presenters are always people.
    """

    # Presenter-related patterns
    PRESENTER_PATTERNS = [
        r"\b(?:presented|presenting|presents?)\s+(?:by\s+)?",
        r"\b(?:introduces?|introduced|introducing)\s+",
        r"\bpresenter(?:s)?\s*(?::|\bis\b)",
        r"\bwill\s+present\b",
        r"\bhanded\s+out\s+the\s+award\b",
    ]

    def __init__(self, min_mentions: int = 3, top_n: int = 2):
        """
        Initialize presenter extractor.

        Args:
            min_mentions: Minimum mention threshold for presenter confidence
            top_n: Number of top presenters to select per award (default 2)
        """
        super().__init__()
        self.min_mentions = min_mentions
        self.top_n = top_n
        self.nlp = get_nlp()
        self.award_presenter_counters: dict[str, Counter] = {}  # Store Counters for candidate extraction

    def match_pattern(self, text: str) -> bool:
        """Check if text mentions presenters."""
        # TODO: use patterns instead of keywords
        keywords = [
            "present",
            "presented",
            "presenting",
            "presenter",
            "presenters",
            "introduces",
            "introduced",
            "introducing",
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)

    def extract_presenters_from_tweet(self, text: str) -> list[str]:
        """
        Extract potential presenter names from a single tweet.

        Presenters are always PERSON entities, not movies or TV shows.

        Args:
            text: Tweet text

        Returns:
            List of normalized presenter names
        """
        presenters = []
        doc = self.nlp(text)

        # Extract only PERSON entities
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                presenters.append(ent.text)

        # Normalize and return
        return [normalize_text(p) for p in presenters if normalize_text(p)]

    def associate_presenters_with_awards(
        self, tweets: list[Tweet], awards: list[str], tweet_awards: dict[int, list[str]] | None = None
    ) -> tuple[dict[str, list[tuple[str, int]]], dict[str, list[Tweet]]]:
        """
        Associate extracted presenters with specific awards.

        Args:
            tweets: List of presenter-related tweets
            awards: List of normalized template award names
            tweet_awards: Optional POS-detected award mentions

        Returns:
            Tuple of:
            - Dictionary mapping award -> [(presenter_name, mention_count), ...]
            - Dictionary mapping award -> [relevant_tweets]
        """
        award_presenters: dict[str, Counter] = defaultdict(Counter)
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

            # Extract presenters from this tweet
            potential_presenters = self.extract_presenters_from_tweet(tweet.text)

            for award in mentioned_awards:
                for presenter in potential_presenters:
                    presenter_normalized = normalize_text(presenter)
                    if presenter_normalized:
                        award_presenters[award][presenter_normalized] += 1

        # Convert to sorted lists
        result = {}
        for award, presenter_counts in award_presenters.items():
            sorted_presenters = presenter_counts.most_common()
            result[award] = sorted_presenters

        return result, award_tweets_map

    def select_top_presenters(
        self, presenter_candidates: list[tuple[str, int]], award_name: str, award_tweets: list[Tweet]
    ) -> list[str]:
        """
        Select the top presenters from candidates.

        Args:
            presenter_candidates: List of (presenter_name, mention_count) tuples
            award_name: Award category name
            award_tweets: Tweets mentioning this award

        Returns:
            List of top presenter names (typically 1-2)
        """
        if not presenter_candidates:
            return []

        # Filter by minimum mentions
        high_confidence = [(name, count) for name, count in presenter_candidates if count >= self.min_mentions]

        # If we have high-confidence presenters, use them
        if high_confidence:
            presenters = [name for name, _ in high_confidence[: self.top_n]]
        else:
            # Otherwise, take top candidates even if below threshold
            # but only if they have at least 2 mentions
            candidates_with_some_confidence = [(name, count) for name, count in presenter_candidates if count >= 2]
            if candidates_with_some_confidence:
                presenters = [name for name, _ in candidates_with_some_confidence[: self.top_n]]
            else:
                presenters = []

        return presenters

    def extract(
        self, tweets: list[Tweet], awards: list[str], tweet_awards: dict[int, list[str]] | None = None
    ) -> dict[str, list[str]]:
        """
        Extract presenters for each award category.

        Args:
            tweets: List of presenter-related tweets
            awards: List of normalized template award names
            tweet_awards: Optional POS-detected award mentions

        Returns:
            Dictionary mapping award name -> list of presenter names
        """
        print(f"Extracting presenters from {len(tweets)} tweets for {len(awards)} awards...")

        if tweet_awards:
            print(f"Using POS-detected awards from {len(tweet_awards)} tweets")

        # Associate presenters with awards
        award_presenter_candidates, award_tweets_map = self.associate_presenters_with_awards(
            tweets, awards, tweet_awards
        )

        # Store raw Counters before filtering (for candidate extraction)
        # Convert from list of tuples back to Counter
        self.award_presenter_counters = {
            award: Counter(dict(candidates)) for award, candidates in award_presenter_candidates.items()
        }

        # Select top presenters for each award
        presenters = {}
        found_count = 0

        for award in awards:
            candidates = award_presenter_candidates.get(award, [])
            award_tweets = award_tweets_map.get(award, [])

            presenter_list = self.select_top_presenters(candidates, award, award_tweets)
            presenters[award] = presenter_list

            if presenter_list:
                found_count += 1

        print(f"✓ Found presenters for {found_count}/{len(awards)} awards")

        return presenters
