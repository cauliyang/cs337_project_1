import json
import random
import zipfile

from rich import print

from award.extract import Extractor
from award.processor import ProcessorPipeline
from award.processors import (
    EmptyTextFilter,
    FtfyCleaner,
    LanguageFilter,
    SpaceCombinationCleaner,
    UnidecodeCleaner,
    UrlCleaner,
)
from award.processors.transformer import HashTagExtractionTransformer, TagUsernameTransformer


def test_read_zip_json():
    with zipfile.ZipFile("data/gg2013.json.zip") as z:
        file_name = z.namelist()[0]
        with z.open(file_name) as f:
            data = json.load(f)
    data = random.sample(data, 10)
    print(data)


def test_extract_with_filters():
    pipeline = ProcessorPipeline(
        [
            FtfyCleaner(),
            UnidecodeCleaner(),
            SpaceCombinationCleaner(),
            UrlCleaner(),
            EmptyTextFilter(),
            LanguageFilter(language="en"),
            HashTagExtractionTransformer(),  # extract and remove hashtags from text
            TagUsernameTransformer(),  # transform hashtags and usernames to human-readable format
        ]
    )
    extractor = Extractor("data/gg2013.json.zip", pipeline=pipeline)

    # count = 0
    # for _tweet in extractor.extract():
    #     count += 1
    #     if count > 10:
    #         break
    import time

    start = time.time()
    total_tweets = len(list(extractor.extract()))
    print(f"Total tweets: {total_tweets}")
    assert total_tweets > 0
    end = time.time()
    print(f"Time taken: {end - start} seconds")
