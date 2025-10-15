import ftfy
import unidecode


class BaseCleaner:
    """Base cleaner class."""

    def __init__(self, cleaner_type: str):
        self.cleaner_type = cleaner_type

    def clean(self, text: str) -> str:
        raise NotImplementedError("Subclasses must implement this method")


class FtfyCleaner(BaseCleaner):
    """Clean text using ftfy."""
    def __init__(self):
        super().__init__(cleaner_type="ftfy text normalization")

    def clean(self, text: str) -> str:
        return ftfy.fix_text(text)


class UnidecodeCleaner(BaseCleaner):
    """Clean text using unidecode."""
    def __init__(self):
        super().__init__(cleaner_type="unidecode text normalization")

    def clean(self, text: str) -> str:
        return unidecode.unidecode(text)

