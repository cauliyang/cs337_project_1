from rich import print

from award.processors import HashTagTransformer, TagUsernameTransformer
from award.tweet import Tweet


def test_hashtag_transformer():
    hashtag_transformer = HashTagTransformer(remove_hashtags=True)
    tweet = Tweet.from_dict(
        {
            "text": "RT @user: This is a tweet with a hashtag #example #example2",
            "user": {"screen_name": "user", "id": 123},
            "id": 123,
            "timestamp_ms": 123,
        }
    )
    print(tweet)
    tweet = hashtag_transformer.process(tweet)
    print(tweet)
    assert tweet.hash_tags == ["#example", "#example2"]

def test_tag_username_transformer():
    tag_username_transformer = TagUsernameTransformer()
    tweet = Tweet.from_dict(
        {
            "text": " #golden_globes #ParksandRec @KateSpencer1 @Stephen_Sondheim",
            "user": {"screen_name": "user", "id": 123},
            "id": 123,
            "timestamp_ms": 123,
        }
    )
    print(tweet)
    tweet = tag_username_transformer.process(tweet)
    print(tweet)
    assert tweet.text == "Golden globes Parksand rec Kate spencer1 Stephen sondheim"