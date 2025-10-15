import json
import zipfile
from abc import ABC, abstractmethod
from collections.abc import Generator
from pathlib import Path

from award.filter import BaseFilter
from award.tweet import Tweet


class BaseCleaner(ABC):
    @abstractmethod
    def clean(self, tweet: str) -> str:
        pass


class Extractor:
    def __init__(self, json_file: str | Path, text_filters: list[BaseFilter], tweet_filters: list[BaseFilter]):
        self.json_file = json_file
        self.text_filters = text_filters
        self.tweet_filters = tweet_filters

    def extract(self) -> Generator[Tweet, None, None]:
        with zipfile.ZipFile(self.json_file) as z:
            file_name = z.namelist()[0]
            with z.open(file_name) as f:
                tweets_dict = json.load(f)

            for tweet_dict in tweets_dict:
                if all(filter.filter(tweet_dict) for filter in self.text_filters):
                    tweet = Tweet.from_dict(tweet_dict)
                    if all(filter.filter(tweet) for filter in self.tweet_filters):
                        yield tweet
