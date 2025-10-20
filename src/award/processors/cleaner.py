import re
from functools import reduce

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


class WhitespaceCollapseCleaner(BaseCleaner):
    """Collapse whitespace from text."""

    def __init__(self):
        super().__init__(processor_type="whitespace collapse")

    def clean(self, text: str) -> str:
        return re.sub(r"\s+", " ", text)


class AlphanumericCleaner(BaseCleaner):
    """Clean text to lowercase + alphanumeric + spaces only."""

    def __init__(self):
        super().__init__(processor_type="alphanumeric")

    def clean(self, text: str) -> str:
        return "".join([c for c in text if c.isalnum() or c.isspace()])


def normalize_text(text: str) -> str:
    """
    Normalize text to match autograder's norm_text() function.

    This function performs the following transformations:
    1. Fix encoding issues using ftfy
    2. Convert unicode characters to ASCII using unidecode
    3. Convert to lowercase
    4. Keep only alphanumeric characters and spaces
    5. Normalize whitespace

    Args:
        text: Original text (e.g., "Daniel Day-Lewis", "Zoë Saldana")

    Returns:
        Normalized text (e.g., "daniel daylewis", "zoe saldana")

    Examples:
        >>> normalize_text("Daniel Day-Lewis")
        'daniel daylewis'
        >>> normalize_text("Zoë Saldana")
        'zoe saldana'
        >>> normalize_text("Best Motion Picture - Drama")
        'best motion picture drama'
    """

    cleaners = [
        FtfyCleaner(),
        UnidecodeCleaner(),
        AlphanumericCleaner(),
        LowercaseCleaner(),
        WhitespaceCollapseCleaner(),
    ]

    return reduce(lambda x, y: y.clean(x), cleaners, text)
