"""Utility functions for text processing and normalization."""

import time
from collections import defaultdict
from functools import reduce

import nltk
import spacy
from spacy.language import Language

from award.processors.cleaner import (
    AlphanumericCleaner,
    FtfyCleaner,
    LowercaseCleaner,
    UnidecodeCleaner,
    WhitespaceCollapseCleaner,
)


def load_nltk_data():
    # Ensure NLTK data is available
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)

    try:
        nltk.data.find("taggers/averaged_perceptron_tagger_eng")
    except LookupError:
        nltk.download("averaged_perceptron_tagger_eng", quiet=True)


def load_nlp_pipeline(model: str = "en_core_web_md", disable: list[str] | None = None) -> Language:
    """
    Load and configure spaCy NLP pipeline.

    Args:
        model: Name of the spaCy model to load (default: en_core_web_md)
        disable: List of pipeline components to disable for performance
                Default disables lemmatizer and textcat which aren't needed
    """
    if disable is None:
        # Disable components we don't need for better performance
        disable = ["lemmatizer", "textcat"]

    nlp = spacy.load(model, disable=disable)
    return nlp


def extract_persons(text: str, nlp: Language) -> list[str]:
    """
    Extract PERSON entities from text using spaCy NER.

    Args:
        text: Input text to analyze
        nlp: Loaded spaCy Language object

    Returns:
        List of person names found in text
    """
    doc = nlp(text)
    persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    return persons


def extract_works_of_art(text: str, nlp: Language) -> list[str]:
    """
    Extract WORK_OF_ART entities (movies, songs, shows) from text.

    Args:
        text: Input text to analyze
        nlp: Loaded spaCy Language object

    Returns:
        List of work of art names found in text
    """
    doc = nlp(text)
    works = [ent.text for ent in doc.ents if ent.label_ == "WORK_OF_ART"]
    return works


def extract_all_entities(text: str, nlp: Language) -> dict[str, list[str]]:
    """
    Extract all named entities from text, grouped by type.

    Args:
        text: Input text to analyze
        nlp: Loaded spaCy Language object

    Returns:
        Dictionary mapping entity labels to lists of entity texts
    """
    doc = nlp(text)
    entities: dict[str, list[str]] = defaultdict(list)

    for ent in doc.ents:
        entities[ent.label_].append(ent.text)

    return entities


# Global NLP pipeline instance (lazy-loaded)
_NLP_PIPELINE: Language | None = None


def get_nlp() -> Language:
    """
    Get or create the global spaCy NLP pipeline instance.

    This function implements lazy loading and caching to avoid
    loading the model multiple times.

    Returns:
        Loaded spaCy Language object
    """
    global _NLP_PIPELINE
    if _NLP_PIPELINE is None:
        _NLP_PIPELINE = load_nlp_pipeline()
    return _NLP_PIPELINE


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


class Timer:
    """Context manager for timing code execution."""

    def __init__(self, message: str):
        self.message = message

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.end = time.time()
        print(f"{self.message} took {self.end - self.start:.2f} seconds")
