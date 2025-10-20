"""Extractors for specific entity types (hosts, awards, winners, nominees, presenters)."""

from .additional_goals_extractor import AdditionalGoalsExtractor
from .award_extractor import AwardExtractor
from .host_extractor import HostExtractor
from .nominee_extractor import NomineeExtractor
from .presenter_extractor import PresenterExtractor
from .winner_extractor import WinnerExtractor

__all__ = [
    "AdditionalGoalsExtractor",
    "AwardExtractor",
    "HostExtractor",
    "NomineeExtractor",
    "PresenterExtractor",
    "WinnerExtractor",
]
