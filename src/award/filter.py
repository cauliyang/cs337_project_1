from abc import ABC, abstractmethod
from functools import singledispatchmethod

import langdetect

from .tweet import Tweet


class BaseFilter(ABC):
    def __init__(self, filter_type: str):
        self.filter_type = filter_type

    @singledispatchmethod
    @abstractmethod
    def filter(self, tweet) -> bool:
        """Filter based on tweet object or string."""
        pass

    @filter.register
    @abstractmethod
    def _(self, tweet: Tweet) -> bool:
        """Filter a Tweet object."""
        pass

    @filter.register
    @abstractmethod
    def _(self, text: str) -> bool:
        """Filter a tweet string."""
        pass


class LanguageFilter(BaseFilter):
    def _(self, text: str) -> bool:
        return langdetect.detect(text) == "en"
