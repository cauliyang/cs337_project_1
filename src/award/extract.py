import json
import zipfile
from collections.abc import Generator
from pathlib import Path

from .processor import BaseProcessor, LoggingPipeline, ProcessorPipeline
from .tweet import Tweet


class Extractor:
    """Extract and process tweets from a JSON file using a processor pipeline.

    The pipeline can contain any combination of filters and cleaners.
    They are applied in sequence to each tweet.

    Example:
        extractor = Extractor(
            "data.json.zip",
            pipeline=ProcessorPipeline([
                FtfyCleaner(),
                EmptyTextFilter(),
                LanguageFilter(),
                RetweetFilter(min_retweets=5)
            ])
        )

        for tweet in extractor.extract():
            print(tweet.text)
    """

    def __init__(
        self,
        json_file: str | Path,
        pipeline: ProcessorPipeline | None = None,
        processors: list[BaseProcessor] | None = None,
        *,
        log: bool = False,
    ):
        """
        Args:
            json_file: Path to JSON file (can be zipped)
            pipeline: A ProcessorPipeline to apply to each tweet
            processors: List of processors (will be wrapped in ProcessorPipeline)
                       Ignored if pipeline is provided.
        """
        self.json_file = Path(json_file)

        if pipeline:
            self.pipeline = pipeline
        elif processors:
            self.pipeline = ProcessorPipeline(processors) if not log else LoggingPipeline(processors)
        else:
            self.pipeline = ProcessorPipeline()

    def extract(self) -> Generator[Tweet, None, None]:
        """Extract tweets, applying the pipeline to each one.

        Yields:
            Tweet objects that pass all filters (after cleaning)
        """
        # check if the file is a zip file
        if self.json_file.suffix == ".zip":
            with zipfile.ZipFile(self.json_file) as z:
                file_name = z.namelist()[0]
                with z.open(file_name) as f:
                    tweets_dict = json.load(f)
        else:
            with open(self.json_file) as f:
                tweets_dict = json.load(f)

        for tweet_dict in tweets_dict:
            try:
                tweet = Tweet.from_dict(tweet_dict)

                # Apply the pipeline (cleaners + filters)
                processed_tweet = self.pipeline.apply(tweet)

                # If pipeline returns None, tweet was filtered out
                if processed_tweet is not None:
                    yield processed_tweet

            except Exception:
                # Skip tweets that cause errors during processing
                continue

    def __call__(self) -> Generator[Tweet, None, None]:
        return self.extract()

    def __repr__(self) -> str:
        return f"Extractor(file={self.json_file.name}, pipeline={self.pipeline})"
