#!/usr/bin/env python
import pydantic
import pytest

from award import tweet


def test_award_fail():
    with pytest.raises(pydantic.ValidationError):
        tweet.Award(name="test award", host=["Tweet"], nominees=["Tweet 1", "Tweet 2", "Tweet 3"], winner="Tweet 4")
