#!/usr/bin/env python
import pydantic
import pytest

from award import tweet


def test_tweet():
    test_tweet = tweet.Tweet(
        raw_txt="This is a test tweet",
        clean_txt="This is a test tweet",
        person="leon",
        hash_tags=["test"],
        retweet_count=0,
    )

    assert test_tweet.raw_txt == "This is a test tweet"


def test_award_fail():
    with pytest.raises(pydantic.ValidationError):
        tweet.Award(name="test award", host=["Tweet"], nominees=["Tweet 1", "Tweet 2", "Tweet 3"], winner="Tweet 4")
