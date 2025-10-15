from functools import singledispatchmethod

import langdetect

from .tweet import Tweet


class BaseFilter:
    """Base filter class with automatic text extraction from Tweet objects.

    Subclasses can implement either or both:
    - filter_text(str) -> bool: for filters that work on text only
    - filter_tweet(Tweet) -> bool: for filters that need the full Tweet object

    By default, filter_tweet() delegates to filter_text() by extracting tweet.text.
    """

    def __init__(self, filter_type: str):
        self.filter_type = filter_type

    @singledispatchmethod
    def filter(self, data) -> bool:
        """Filter based on tweet object or string."""
        raise NotImplementedError(f"Filter not implemented for type {type(data)}")

    @filter.register
    def _(self, tweet: Tweet) -> bool:
        """Filter a Tweet object. Delegates to filter_tweet."""
        return self.filter_tweet(tweet)

    @filter.register
    def _(self, text: str) -> bool:
        """Filter a text string. Delegates to filter_text."""
        return self.filter_text(text)

    def filter_tweet(self, tweet: Tweet) -> bool:
        """Filter based on Tweet object. Default: extract text and use filter_text.

        Override this method if your filter needs Tweet metadata (retweet_count, user, etc.)
        """
        return self.filter_text(tweet.text)

    def filter_text(self, text: str) -> bool:
        """Filter based on text. Override this for text-based filters.

        Raises NotImplementedError if not overridden and filter(str) is called.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support text-only filtering. "
            f"Use Tweet objects or override filter_text()."
        )


class EmptyTextFilter(BaseFilter):
    """Filter that always returns True."""

    def __init__(self):
        super().__init__(filter_type="empty string")

    def filter_text(self, text: str) -> bool:
        return bool(text and text.strip())


class LanguageFilter(BaseFilter):
    """Filter tweets based on language detection."""

    def __init__(self):
        super().__init__(filter_type="language")

    def filter_text(self, text: str) -> bool:
        """Check if text is in English. Returns False for invalid input."""
        return langdetect.detect(text) == "en"


class RetweetFilter(BaseFilter):
    """Filter tweets based on retweet count. Only works with Tweet objects."""

    def __init__(self, min_retweets: int = 0):
        super().__init__(filter_type="retweet")
        self.min_retweets = min_retweets

    def filter_tweet(self, tweet: Tweet) -> bool:
        """Filter based on retweet count. Only works with Tweet objects."""
        return tweet.retweet_count >= self.min_retweets
