from award.filter import UrlCleaner
from award.tweet import Tweet


def test_link_cleaner():
    link_cleaner = UrlCleaner()
    test_tweet = Tweet.from_dict(
        {
            "text": 'RT @TheWeek: Lena Dunham "promised she would thank Chad Lowe," for reasons probably best left unexplained.  http://t.co/pDiyf1PG',  # noqa: E501
            "user": {"screen_name": "mchasewalker", "id": 19698370},
            "id": 290661110032506880,
            "timestamp_ms": 1358133983000,
        }
    )

    cleaned_tweet = link_cleaner.process(test_tweet)
    assert (
        cleaned_tweet.text
        == 'RT @TheWeek: Lena Dunham "promised she would thank Chad Lowe," for reasons probably best left unexplained.'
    )
