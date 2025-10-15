"""Unified processor architecture for Filters, Cleaners, and Transformers."""

from abc import ABC, abstractmethod
from functools import singledispatchmethod
from typing import Any

from rich import print

from .tweet import Tweet


class BaseProcessor(ABC):
    """Base class for all data processors (filters, cleaners, transformers).

    Processors can operate on text strings or Tweet objects and are composable.
    """

    def __init__(self, processor_type: str):
        self.processor_type = processor_type

    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process the input data. Override in subclasses."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.processor_type})"


class BaseFilter(BaseProcessor):
    """Base filter class that returns bool (pass/fail).

    Filters decide whether to keep or reject data.
    """

    @singledispatchmethod
    def process(self, data: Any) -> Any:  # type: ignore[override]
        """Process and return True to keep, False to reject."""
        raise NotImplementedError(f"Filter not implemented for type {type(data)}")

    @process.register
    def _(self, tweet: Tweet) -> bool:
        """Filter a Tweet object. Delegates to filter_tweet."""
        return self.filter_tweet(tweet)

    @process.register
    def _(self, text: str) -> bool:
        """Filter a text string. Delegates to filter_text."""
        return self.filter_text(text)

    def filter_tweet(self, tweet: Tweet) -> bool:
        """Filter based on Tweet object. Default: extract text and use filter_text."""
        return self.filter_text(tweet.text)

    def filter_text(self, text: str) -> bool:
        """Filter based on text. Override this for text-based filters."""
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support text-only filtering. "
            f"Use Tweet objects or override filter_text()."
        )

    def __call__(self, data) -> bool:
        """Allows using filter(data) or filter.process(data)."""
        return self.process(data)


class BaseCleaner(BaseProcessor):
    """Base cleaner class that transforms text (str -> str).

    Cleaners normalize, fix, or transform text data.
    """

    @abstractmethod
    def clean(self, text: str) -> str:
        """Clean/transform the text. Override in subclasses."""
        pass

    def process(self, data: str | Tweet) -> str | Tweet:
        """Process text or Tweet by cleaning the text content."""
        if isinstance(data, Tweet):
            data.text = self.clean(data.text)
            return data
        elif isinstance(data, str):
            return self.clean(data)
        else:
            raise TypeError(f"Cleaner cannot process {type(data)}")

    def __call__(self, data: str | Tweet) -> str | Tweet:
        """Allows using cleaner(data) or cleaner.process(data)."""
        return self.process(data)


class ProcessorPipeline:
    """A composable pipeline of processors (filters and cleaners).

    Processors are applied in sequence:
    - Cleaners transform the data
    - Filters decide whether to keep the data

    Example:
        pipeline = ProcessorPipeline([
            FtfyCleaner(),
            UnidecodeCleaner(),
            EmptyTextFilter(),
            LanguageFilter(),
            RetweetFilter(min_retweets=5)
        ])

        # Apply to a tweet
        tweet = pipeline.apply(raw_tweet)  # Returns tweet or None if filtered out
    """

    def __init__(self, processors: list[BaseProcessor] | None = None):
        self.processors = processors or []

    def add(self, processor: BaseProcessor) -> "ProcessorPipeline":
        """Add a processor to the pipeline. Returns self for chaining."""
        self.processors.append(processor)
        return self

    def apply(self, data: str | Tweet) -> str | Tweet | None:
        """Apply all processors in sequence.

        Returns:
            - For filters: continues if True, returns None if False
            - For cleaners: returns transformed data
            - None if any filter returns False
        """
        result = data
        for processor in self.processors:
            if isinstance(processor, BaseFilter):
                # Filters return bool - stop if False
                if not processor.process(result):
                    return None
            elif isinstance(processor, BaseCleaner):
                # Cleaners transform the data
                result = processor.process(result)
            else:
                # Generic processor
                result = processor.process(result)
        return result

    def __len__(self) -> int:
        return len(self.processors)

    def __repr__(self) -> str:
        return f"ProcessorPipeline({len(self.processors)} processors)"


class LoggingPipeline(ProcessorPipeline):
    """Pipeline with detailed logging of each processing step."""

    def apply(self, data: str | Tweet) -> str | Tweet | None:
        result = data
        print(f"\nApplying pipeline to {data}")
        for i, processor in enumerate(self.processors):
            print(f"Step {i}: {processor}")

            if isinstance(processor, BaseFilter):
                # Filters return bool - check the result
                passed = processor.process(result)
                print(f"  → Filter result: {passed}")
                if not passed:
                    print(f"  → Filtered out by {processor}")
                    return None
                # Keep the current result (don't replace with bool)
            elif isinstance(processor, BaseCleaner):
                # Cleaners transform the data
                result = processor.process(result)
                if isinstance(result, Tweet):
                    print(f"  → Cleaned text: {result.text[:50]}...")
                else:
                    print(f"  → Cleaned text: {result[:50]}...")
            else:
                # Generic processor
                result = processor.process(result)

        return result
