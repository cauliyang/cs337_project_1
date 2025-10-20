import re
from collections import defaultdict

from inflection import humanize, underscore

from award.processor import BaseProcessor
from award.tweet import Tweet


class HashTagExtractionTransformer(BaseProcessor):
    """Transform the hashtags in the tweet.

    Extracts only hashtags appearing at the end of the tweet text and removes them from the text.
    """

    _hashtags_pattern = re.compile(r"(#\w+\s*)+$")
    _hashtag_pattern = re.compile(r"#\w+")

    def __init__(self, *, remove_hashtags: bool = True):
        super().__init__(processor_type="hashtag transformer")
        # WARNING: whether to remove the hashtags from the tweet text
        # edge case: “I wanna see #AmyPoehler win one of these days for #ParksandRec
        self.remove_hashtags = remove_hashtags

    def process(self, tweet: Tweet) -> Tweet:
        """Extracts only hashtags appearing at the end of the tweet text and removes them from the text."""
        # Find hashtags at the end (contiguous #tags at end, possibly after some whitespace)
        match = re.search(self._hashtags_pattern, tweet.text)
        if match:
            tweet.hash_tags = re.findall(self._hashtag_pattern, match.group())
            if self.remove_hashtags:
                # Remove the matched hashtags from the end of the text
                tweet.text = tweet.text[: match.start()].rstrip()
        return tweet

    def transform_tags(self, tags: list[str]) -> list[str]:
        """Transform the hashtags."""
        raise NotImplementedError("Not implemented")


class TagUsernameTransformer(BaseProcessor):
    """
    Transform hashtags and usernames in the tweet text to a more human-readable format.

    Examples:
        "#golden_globes" -> "golden globes"
        "#ParksandRec" -> "Parksand rec"
        "@KateSpencer1" -> "Kate spencer1"
        "@Stephen_Sondheim" -> "Stephen sondheim"
    """

    _username_pattern = re.compile(r"@\w+")
    _hashtag_pattern = re.compile(r"#\w+")

    def __init__(self):
        super().__init__(processor_type="tag username transformer")

    def process(self, tweet: Tweet) -> Tweet:
        """Transform hashtags and usernames in the tweet text."""
        # Delayed import for performance if unused

        def username_repl(m):
            username = m.group()[1:]  # Remove '@'
            username_human = humanize(username) if "_" in username else humanize(underscore(username))

            return f"{username_human}"

        def hashtag_repl(m):
            hashtag = m.group()[1:]  # Remove '#'
            hashtag_human = humanize(hashtag) if "_" in hashtag else humanize(underscore(hashtag))
            return f"{hashtag_human}"

        # Use sub only if patterns are present for efficiency
        text = tweet.text
        if "@" in text:
            text = self._username_pattern.sub(username_repl, text)
        if "#" in text:
            text = self._hashtag_pattern.sub(hashtag_repl, text)
        tweet.text = text

        return tweet
