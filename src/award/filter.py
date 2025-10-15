import re

import ftfy
import langdetect
import unidecode

from .processor import BaseCleaner, BaseFilter
from .tweet import Tweet

# CLEANERS (str -> str transformations)


class FtfyCleaner(BaseCleaner):
    """Clean text using ftfy to fix unicode issues."""

    def __init__(self):
        super().__init__(processor_type="ftfy normalization")

    def clean(self, text: str) -> str:
        return ftfy.fix_text(text)


class UnidecodeCleaner(BaseCleaner):
    """Convert unicode to ASCII using unidecode."""

    def __init__(self):
        super().__init__(processor_type="unidecode normalization")

    def clean(self, text: str) -> str:
        return unidecode.unidecode(text)


class LowercaseCleaner(BaseCleaner):
    """Convert text to lowercase."""

    def __init__(self):
        super().__init__(processor_type="lowercase")

    def clean(self, text: str) -> str:
        return text.lower()


class StripCleaner(BaseCleaner):
    """Strip whitespace from text."""

    def __init__(self):
        super().__init__(processor_type="strip whitespace")

    def clean(self, text: str) -> str:
        return text.strip()


class UrlCleaner(BaseCleaner):
    """Clean URLs from text."""

    def __init__(self):
        super().__init__(processor_type="url cleaner")

    def clean(self, text: str) -> str:
        return re.sub(r"https?://\S+", "", text)


class SpaceCombinationCleaner(BaseCleaner):
    """Clean space combinations from text."""

    def __init__(self):
        super().__init__(processor_type="space combination cleaner")

    def clean(self, text: str) -> str:
        return re.sub(r"\s+", " ", text)


# FILTERS (returns bool for pass/fail)


class EmptyTextFilter(BaseFilter):
    """Filter out empty or whitespace-only text."""

    def __init__(self):
        super().__init__(processor_type="empty text")

    def filter_text(self, text: str) -> bool:
        return bool(text and text.strip())


class LanguageFilter(BaseFilter):
    """Filter tweets based on language detection."""

    def __init__(self, language: str = "en"):
        super().__init__(processor_type=f"language={language}")
        self.language = language

    def filter_text(self, text: str) -> bool:
        """Check if text is in the specified language.

        Raises:
            langdetect.lang_detect_exception.LangDetectException: If the language detection fails.
        """
        if not text or not text.strip():
            return False

        return langdetect.detect(text) == self.language


class RetweetFilter(BaseFilter):
    """Filter tweets based on retweet count. Only works with Tweet objects."""

    def __init__(self, min_retweets: int = 0):
        super().__init__(processor_type=f"min_retweets={min_retweets}")
        self.min_retweets = min_retweets

    def filter_tweet(self, tweet: Tweet) -> bool:
        """Filter based on retweet count."""
        return tweet.retweet_count >= self.min_retweets


class MinLengthFilter(BaseFilter):
    """Filter out text shorter than minimum length."""

    def __init__(self, min_length: int = 10):
        super().__init__(processor_type=f"min_length={min_length}")
        self.min_length = min_length

    def filter_text(self, text: str) -> bool:
        return len(text) >= self.min_length


class KeywordFilter(BaseFilter):
    """Filter text containing specific keywords."""

    def __init__(self, keywords: list[str], case_sensitive: bool = False):
        super().__init__(processor_type=f"keywords={len(keywords)}")
        self.keywords = keywords
        self.case_sensitive = case_sensitive

    def filter_text(self, text: str) -> bool:
        """Return True if text contains any keyword."""
        search_text = text if self.case_sensitive else text.lower()
        search_keywords = self.keywords if self.case_sensitive else [k.lower() for k in self.keywords]
        return any(keyword in search_text for keyword in search_keywords)
