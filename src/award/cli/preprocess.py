from pathlib import Path

from award.extract import Extractor
from award.processor import ProcessorPipeline
from award.processors import (
    EmptyTextFilter,
    FtfyCleaner,
    KeywordFilter,
    TagUsernameTransformer,
    UnidecodeCleaner,
    UrlCleaner,
    WhitespaceCollapseCleaner,
)
from award.processors.filter import GroupTweetsFilter
from award.processors.transformer import HashTagExtractionTransformer
from award.utils import Timer


def main(input_file: Path, output_file: Path):
    text_pipeline = ProcessorPipeline(
        [
            FtfyCleaner(),
            UnidecodeCleaner(),
            WhitespaceCollapseCleaner(),
            UrlCleaner(),
            EmptyTextFilter(),
            # LanguageFilter(language="en"),  # WARNING: took longer time and can increse > 20 times
            HashTagExtractionTransformer(),  # extract and remove hashtags from text
            TagUsernameTransformer(),  # transform hashtags and usernames to human-readable format
        ]
    )

    group_filter = GroupTweetsFilter()
    group_pipeline = ProcessorPipeline([KeywordFilter(keywords=["RT"], case_sensitive=True), group_filter])
    extractor = Extractor(input_file, pipeline=group_pipeline + text_pipeline)

    with Timer("Extracting and preprocessing tweets"):
        tweets = list(extractor.extract())
        total_tweets = len(list(extractor.extract()))
        print(f"Total tweets after preprocessing: {total_tweets}")

    for group, tweets in group_filter.groups.items():
        print(f"Group: {group}, Count: {len(tweets)}")
