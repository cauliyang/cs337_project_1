import re

import ftfy
import unidecode

from award.processor import BaseCleaner


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
