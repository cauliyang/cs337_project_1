import re
from collections import defaultdict

import langdetect
import nltk
from nltk import RegexpParser, pos_tag, word_tokenize

from award.processor import BaseFilter
from award.tweet import Tweet
from award.utils import load_nltk_data


# FILTERS (returns bool for pass/fail)
class EmptyTextFilter(BaseFilter):
    """Filter out empty or whitespace-only text."""

    def __init__(self):
        super().__init__(processor_type="empty text")

    def filter_text(self, text: str) -> bool:
        return bool(text and text.strip())


class LanguageFilter(BaseFilter):
    """Filter tweets based on language detection."""

    def __init__(self, language: str = "en"):
        super().__init__(processor_type=f"language={language}")
        self.language = language

    def filter_text(self, text: str) -> bool:
        """Check if text is in the specified language.

        Raises:
            langdetect.lang_detect_exception.LangDetectException: If the language detection fails.
        """
        if not text or not text.strip():
            return False

        return langdetect.detect(text) == self.language


class RetweetFilter(BaseFilter):
    """Filter tweets based on retweet count. Only works with Tweet objects."""

    def __init__(self, min_retweets: int = 0):
        super().__init__(processor_type=f"min_retweets={min_retweets}")
        self.min_retweets = min_retweets

    def filter_tweet(self, tweet: Tweet) -> bool:
        """Filter based on retweet count."""
        return tweet.retweeted_count >= self.min_retweets


class MinLengthFilter(BaseFilter):
    """Filter out text shorter than minimum length."""

    def __init__(self, min_length: int = 10):
        super().__init__(processor_type=f"min_length={min_length}")
        self.min_length = min_length

    def filter_text(self, text: str) -> bool:
        return len(text) >= self.min_length


class KeywordFilter(BaseFilter):
    """Filter text containing specific keywords."""

    def __init__(self, keywords: list[str], case_sensitive: bool = False):
        super().__init__(processor_type=f"keywords({len(keywords)})={keywords}")
        self.keywords = keywords
        self.case_sensitive = case_sensitive

    def filter_text(self, text: str) -> bool:
        """Return False if text contains any keyword."""
        search_text = text if self.case_sensitive else text.lower()
        search_keywords = self.keywords if self.case_sensitive else [k.lower() for k in self.keywords]
        return not any(keyword in search_text for keyword in search_keywords)


class GroupTweetsFilter(BaseFilter):
    """Filter and Group tweets with POS-based award detection"""

    _win_pattern = re.compile(r"\bwin(s|ning|ner|ners)?|won\b", re.IGNORECASE)
    _host_pattern = re.compile(r"\bhost(s|ed|ing)?\b", re.IGNORECASE)
    # Expanded presenter pattern: include various presentation contexts
    _presenter_pattern = re.compile(
        r"\bpresent(s|ed|ing|er|ers)?|"
        r"\bintroduc(e|es|ed|ing)|"
        r"\bannouncing\s+(the\s+)?(winner|award)|"
        r"\bgiv(e|es|ing)\s+(out\s+)?(the\s+)?award|"
        r"\bhanded\s+out|"
        r"\bon\s+stage\s+to",
        re.IGNORECASE,
    )
    # Expanded nominee pattern: include nomination keywords + prediction/comparison contexts
    # Now safe to overlap with _win_pattern since tweets can be in multiple groups
    _nominee_pattern = re.compile(
        r"\bnominat(e|es|ed|ing|ion|ions)|nominee(s)?|"
        r"\bcontender(s)?|"
        r"\bshould\s+(win|have\s+won)|"
        r"\bdeserves?\s+to\s+win|"
        r"\bup\s+for\s+(best|the)|"
        r"\bin\s+the\s+(running|race)|"
        r"\bhoping\s+.+\s+wins?|"
        r"\brooting\s+for|"
        r"\bpredicting?\s+.+\s+(to\s+)?win",
        re.IGNORECASE,
    )
    _cecil_pattern = re.compile(r"\bcecil\s+b\.?\s+demille\s+award\b", re.IGNORECASE)

    # POS-based grammar for award extraction
    # Pattern: Best (RBS/JJS) + optional adjectives/nouns + prepositions + more modifiers
    AWARD_GRAMMAR = r"""
        AWARD: {<RBS|JJS><VBG>?<JJ.*>*<NN.*>+<IN>?<DT>?<JJ.*>*<NN.*>*<IN>?<DT>?<JJ.*>*<NN.*>*}
    """

    def __init__(self):
        super().__init__(processor_type="filter and group by info")
        self.groups: dict[str, list[Tweet]] = defaultdict(list)
        self.tweet_awards: dict[int, list[str]] = {}  # tweet_id -> [award_names]

        load_nltk_data()

        # Initialize chunk parser
        self.chunk_parser = RegexpParser(self.AWARD_GRAMMAR)

    def extract_award_mentions(self, text: str) -> list[str]:
        """
        Extract award mentions from tweet text using POS tagging and chunking.

        Args:
            text: Tweet text

        Returns:
            List of award phrases found in the tweet
        """
        awards = []

        # Special case: Cecil B. DeMille Award (preserve periods)
        if self._cecil_pattern.search(text):
            awards.append("cecil b. demille award")

        try:
            # Tokenize and POS tag
            tokens = word_tokenize(text.lower())
            pos_tagged = pos_tag(tokens)

            # Parse with chunk grammar
            tree = self.chunk_parser.parse(pos_tagged)

            # Extract AWARD chunks
            for subtree in tree:
                if isinstance(subtree, nltk.Tree) and subtree.label() == "AWARD":
                    # Extract words from the chunk
                    award_words = [word for word, tag in subtree.leaves()]
                    award_phrase = " ".join(award_words)

                    # Filter: must contain "best" and be reasonable length
                    if award_phrase and "best" in award_phrase and 10 < len(award_phrase) < 100:
                        awards.append(award_phrase)

        except Exception:
            # If POS tagging fails, fall back to simple pattern
            pass

        return awards

    def filter_tweet(self, tweet: Tweet) -> bool:
        """Filter and group tweets, extracting award mentions for all relevant categories.

        Note: Tweets can belong to multiple groups (e.g., both 'win' and 'nominee').
        """
        # Extract award mentions once for efficiency
        award_mentions = self.extract_award_mentions(tweet.text)
        matched = False

        # Check all patterns - allow tweets to be in multiple groups
        if re.search(self._win_pattern, tweet.text):
            self.groups["win"].append(tweet)
            # Store award mentions for better association
            if award_mentions:
                if tweet.id not in self.tweet_awards:
                    self.tweet_awards[tweet.id] = []
                self.tweet_awards[tweet.id].extend(award_mentions)

            matched = True

        if re.search(self._host_pattern, tweet.text):
            self.groups["host"].append(tweet)
            matched = True

        if re.search(self._presenter_pattern, tweet.text):
            self.groups["presenter"].append(tweet)
            # Store award mentions for presenters too
            if award_mentions:
                if tweet.id not in self.tweet_awards:
                    self.tweet_awards[tweet.id] = []
                self.tweet_awards[tweet.id].extend(award_mentions)
            matched = True

        if re.search(self._nominee_pattern, tweet.text):
            self.groups["nominee"].append(tweet)
            # Store award mentions for nominees too
            if award_mentions:
                if tweet.id not in self.tweet_awards:
                    self.tweet_awards[tweet.id] = []
                self.tweet_awards[tweet.id].extend(award_mentions)
            matched = True

        return matched
