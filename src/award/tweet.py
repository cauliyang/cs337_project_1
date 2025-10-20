import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, TypeAdapter, model_validator


class User(BaseModel):
    """
    A data model representing a user.
    """

    id: int = Field(..., description="The ID of the user.")
    screen_name: str = Field(..., description="The screen name of the user.")


class Tweet(BaseModel):
    """
    A data model representing a Tweet with both raw and cleaned text,
    user information, hashtags, and engagement metrics.
    """

    id: int = Field(..., description="The ID of the tweet.")
    text: str = Field(..., description="The original, unprocessed text of the tweet.")
    user: User = Field(..., description="User information.")
    timestamp_ms: int = Field(..., description="The timestamp (ms) of the tweet.", repr=False)
    timestamp_human: str = Field(
        default="",
        description="Human-readable timestamp.",
    )
    hash_tags: list[str] = Field(default_factory=list, description="List of hashtags included in the tweet.")
    retweeted_count: int = Field(
        default=0, ge=0, description="Number of times this tweet has been retweeted (non-negative)."
    )

    model_config = {
        "title": "Tweet Model",
        "extra": "ignore",  # Ignore unknown fields for safety
        "validate_assignment": True,  # Enable validation when attributes are modified
        "str_strip_whitespace": True,  # Trim whitespace in all string fields
    }

    def __init__(self, **data):
        super().__init__(**data)
        dt = datetime.fromtimestamp(self.timestamp_ms / 1000)
        self.timestamp_human = dt.strftime("%Y-%m-%d %H:%M:%S")

    def has_tag(self, tag: str) -> bool:
        """Check if the tweet contains a specific hashtag."""
        return tag in self.hash_tags

    def is_retweet(self) -> bool:
        """Check if the tweet is a retweet or quote retweet."""
        return self.text.startswith("RT @")

    def is_quote_tweet(self) -> bool:
        """Check if the tweet is a quote tweet."""
        return "RT @" in self.text

    @classmethod
    def from_dict(cls, data: dict) -> "Tweet":
        """Create a Tweet object from a dictionary.

        Example:
            {
            'text': 'It was awkward. RT @hollywoodhwife: They cut to and then from JLo during the Ben Affleck interview.
        #goldenglobes',
            'user': {'screen_name': 'KateSpencer1', 'id': 21571382},
            'id': 290620657560084480,
            'timestamp_ms': 1358124338000
            }
        """
        user_data = data["user"]
        return Tweet(
            text=data["text"],
            user=User(id=user_data["id"], screen_name=user_data["screen_name"]),
            id=data["id"],
            timestamp_ms=data["timestamp_ms"],
        )


TweetListAdapter = TypeAdapter(list[Tweet])


class Award(BaseModel):
    name: str = Field(..., description="Name of the award category")
    host: list[str] = Field(..., description="List of hosts for the award ceremony")
    presenters: list[str] = Field(..., description="List of presenters for the award")
    nominees: list[str] = Field(..., description="List of nominees for the award")
    winner: str = Field(..., description="Winner of the award")

    model_config = {
        "title": "Award Model",
        "extra": "ignore",  # Ignore unknown fields
        "validate_assignment": True,  # Validate on assignment
        "str_strip_whitespace": True,  # Trim whitespace in string fields
    }

    @model_validator(mode="after")
    def validate_winner_in_nominees(self):
        """
        Validate that the winner is included in the list of nominees.
        Raises:
            ValueError: if the winner is not one of the nominees.
        """
        if self.winner not in self.nominees:
            raise ValueError(f"The winner '{self.winner}' must be one of the nominees: {', '.join(self.nominees)}.")
        return self


def load_tweets(file_path: str) -> list[Tweet]:
    """
    Load tweets from a JSON file.

    Args:
        file_path: Path to the JSON file containing tweets

    Returns:
        List of Tweet objects

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Tweet file not found: {file_path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Handle both list of tweets and dict with tweets key
    if isinstance(data, dict) and "tweets" in data:
        data = data["tweets"]

    # Convert to Tweet objects
    tweets = [Tweet.from_dict(tweet_data) for tweet_data in data]

    return tweets
