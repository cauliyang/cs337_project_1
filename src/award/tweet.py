from pydantic import BaseModel, Field, model_validator


class Tweet(BaseModel):
    """
    A data model representing a Tweet with both raw and cleaned text,
    user information, hashtags, and engagement metrics.
    """

    raw_txt: str = Field(..., description="The original, unprocessed text of the tweet.")
    clean_txt: str = Field(..., description="The cleaned or preprocessed version of the tweet text.")
    person: str = Field(..., description="Username or identifier of the person who posted the tweet.")
    hash_tags: list[str] = Field(default_factory=list, description="List of hashtags included in the tweet.")
    retweet_count: int = Field(0, ge=0, description="Number of times this tweet has been retweeted (non-negative).")

    model_config = {
        "title": "Tweet Model",
        "extra": "ignore",  # Ignore unknown fields for safety
        "validate_assignment": True,  # Enable validation when attributes are modified
        "str_strip_whitespace": True,  # Trim whitespace in all string fields
    }

    def has_tag(self, tag: str) -> bool:
        """Check if the tweet contains a specific hashtag."""
        return tag in self.hash_tags


class Award(BaseModel):
    name: str = Field(..., description="Name of the award category")
    host: list[str] = Field(..., description="List of hosts for the award ceremony")
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
