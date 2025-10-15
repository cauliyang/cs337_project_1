from award.processor import LoggingPipeline
from award.filter import UrlCleaner
from award.filter import SpaceCombinationCleaner
import json
import zipfile

from rich import print

from award.extract import Extractor
from award.filter import EmptyTextFilter, FtfyCleaner, LanguageFilter, StripCleaner, UnidecodeCleaner
from award.processor import ProcessorPipeline


def test_read_zip_json():
    with zipfile.ZipFile("data/gg2013.json.zip") as z:
        file_name = z.namelist()[0]
        with z.open(file_name) as f:
            data = json.load(f)
    print(data[:10])


def test_extract_with_filters():
    pipeline = LoggingPipeline(
        [
            StripCleaner(),
            FtfyCleaner(),
            UnidecodeCleaner(),
            SpaceCombinationCleaner(),
            UrlCleaner(),
            EmptyTextFilter(),
            LanguageFilter(language="en"),
        ]
    )
    extractor = Extractor("data/gg2013.json.zip", pipeline=pipeline)

    count = 0
    for tweet in extractor.extract():
        print(tweet)
        count += 1
        if count > 10:
            break

    # total_tweets = len(list(extractor.extract()))
    # print(f"Total tweets: {total_tweets}")
    # assert total_tweets > 0



