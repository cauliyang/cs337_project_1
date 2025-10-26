"""Entity type validator for distinguishing person vs. work entities."""

from typing import Literal


class EntityTypeValidator:
    """
    Validate and determine entity types (person vs. movie/show/song).

    Uses multiple signals:
    - Award category context
    - Capitalization patterns
    - Common name databases
    - Quote marks and formatting
    """

    # Common first names database (sample - can be extended)
    # TODO: detect person names from cinemagoer
    COMMON_FIRST_NAMES = {
        "jennifer",
        "daniel",
        "anne",
        "ben",
        "hugh",
        "jessica",
        "amy",
        "tina",
        "george",
        "brad",
        "angelina",
        "matt",
        "meryl",
        "robert",
        "tom",
        "leonardo",
        "scarlett",
        "denzel",
        "morgan",
        "samuel",
        "will",
        "chris",
        "ryan",
        "emma",
        "natalie",
        "charlize",
        "kate",
        "julia",
        "sandra",
        "johnny",
        "christian",
        "harrison",
        "sean",
        "kevin",
        "michael",
        "helen",
        "cate",
        "nicole",
        "julianne",
        "adele",
        "taylor",
        "katy",
        "rihanna",
        "beyonce",
        "britney",
        "bradley",
        "mark",
        "joaquin",
        "javier",
        "christoph",
        "marion",
        "penelope",
        "salma",
        "halle",
        "viola",
        "eddie",
        "colin",
        "jude",
        "ewan",
        "rachel",
        "jodie",
        "sally",
        "glenn",
        "diane",
        "frances",
        "tilda",
        "damien",
        "quentin",
        "martin",
        "steven",
        "christopher",
        "david",
        "peter",
        "ridley",
        "kathryn",
        "sofia",
    }

    EntityType = Literal["person", "movie", "tv_show", "song", "unknown"]

    def __init__(self):
        """Initialize entity type validator."""
        pass

    def get_expected_type_from_award(self, award_name: str) -> EntityType:
        """
        Determine expected entity type from award category name.

        Args:
            award_name: Normalized award name

        Returns:
            Expected entity type
        """
        award_lower = award_name.lower()

        # Person awards (actors, directors, etc.)
        if any(word in award_lower for word in ["actor", "actress", "director", "performance"]):
            return "person"

        # Motion picture awards (movies)
        if "motion picture" in award_lower and "performance" not in award_lower:
            # All motion picture awards expect movie titles as nominees/winners
            # (even for screenplay, score - the movie wins, not the writer/composer)
            return "movie"

        # TV awards
        if any(phrase in award_lower for phrase in ["television series", "mini-series", "miniseries"]):
            if "performance" in award_lower:
                return "person"
            return "tv_show"

        # Song awards
        if "song" in award_lower:
            return "song"

        # Animated/foreign film
        if "film" in award_lower or "feature" in award_lower:
            return "movie"

        return "unknown"

    def has_person_name_pattern(self, entity: str) -> bool:
        """
        Check if entity looks like a person name.

        Args:
            entity: Entity string

        Returns:
            True if looks like person name
        """
        if not entity:
            return False

        # Check first word against common names
        words = entity.strip().lower().split()
        if not words:
            return False

        first_name = words[0]
        return first_name in self.COMMON_FIRST_NAMES

    def has_work_indicators(self, text: str, entity: str) -> bool:
        """
        Check if entity appears with work title indicators in text.

        Args:
            text: Full tweet text
            entity: Entity to check

        Returns:
            True if entity appears as work title
        """
        # Check for quotes around entity
        if f'"{entity}"' in text or f"'{entity}'" in text:
            return True

        # Check for hashtag version (common for movie/show titles)
        hashtag_version = "#" + entity.replace(" ", "")
        if hashtag_version.lower() in text.lower():
            return True

        return False

    def title_case_ratio(self, entity: str) -> float:
        """
        Calculate ratio of title-cased words.

        Args:
            entity: Entity string

        Returns:
            Ratio of title-cased words (0-1)
        """
        words = entity.split()
        if not words:
            return 0.0

        title_case_count = sum(1 for word in words if word and word[0].isupper())

        return title_case_count / len(words)

    def classify(self, entity: str, award_name: str, tweet_text: str = "") -> EntityType:
        """
        Classify entity type using multiple signals.

        Args:
            entity: Entity to classify
            award_name: Award category name (for context)
            tweet_text: Original tweet text (optional, for context)

        Returns:
            Classified entity type
        """
        # Signal 1: Award category (highest weight)
        expected_type = self.get_expected_type_from_award(award_name)
        if expected_type != "unknown":
            # Strong signal - trust award category unless other signals contradict

            # Check for person name pattern
            looks_like_person = self.has_person_name_pattern(entity)

            # For ambiguous technical awards, use name pattern
            if expected_type in ["movie", "tv_show", "song"]:
                if looks_like_person:
                    # Might be composer/writer name instead of work title
                    # For scores/songs, often the artist wins, not the song title
                    if "score" in award_name or "song" in award_name:
                        # Check if entity appears as work in tweet
                        if tweet_text and self.has_work_indicators(tweet_text, entity):
                            return expected_type  # It's the work title
                        return "person"  # Likely the artist/composer

                    # For picture/series awards, if it looks like a person name,
                    # check if there are work indicators (quotes, hashtags)
                    # If no work indicators, it's likely a person, not a work
                    if tweet_text and not self.has_work_indicators(tweet_text, entity):
                        return "person"  # Person name, not movie/show title

            return expected_type

        # Signal 2: Person name pattern
        if self.has_person_name_pattern(entity):
            return "person"

        # Signal 3: Work indicators in tweet
        if tweet_text and self.has_work_indicators(tweet_text, entity):
            return "movie"  # Generic work type

        # Signal 4: Title case ratio
        # Both persons and works use title case, so this is weak
        ratio = self.title_case_ratio(entity)
        if ratio < 0.5:
            # Lowercase or mixed - probably not a proper entity
            return "unknown"

        # Default: unknown
        return "unknown"

    def filter_by_type(
        self, entities: list[str], expected_type: EntityType, award_name: str, tweet_texts: list[str] | None = None
    ) -> list[str]:
        """
        Filter entities to keep only those matching expected type.

        Args:
            entities: List of entity names
            expected_type: Expected entity type
            award_name: Award category name
            tweet_texts: Optional list of tweet texts for context

        Returns:
            Filtered list of entities
        """
        filtered = []

        for i, entity in enumerate(entities):
            tweet_text = tweet_texts[i] if tweet_texts and i < len(tweet_texts) else ""

            entity_type = self.classify(entity, award_name, tweet_text)

            # Keep if matches expected type or unknown (benefit of doubt)
            if entity_type == expected_type or entity_type == "unknown":
                filtered.append(entity)

        return filtered
