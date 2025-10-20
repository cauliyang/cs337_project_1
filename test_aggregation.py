#!/usr/bin/env python3
"""
Simple test script to demonstrate the aggregation feature.
"""

from src.award.aggregate import AwardAggregator, AggregationStrategy
from src.award.tweet import Tweet, User


def test_aggregation():
    """Test the aggregation functionality with mock data."""
    print("Testing Award Aggregation Feature")
    print("=" * 40)
    
    # Create mock tweets with different retweet counts
    mock_tweets = [
        Tweet(id=1, text="Daniel Day-Lewis wins Best Actor!", 
              user=User(id=1, screen_name="user1"), timestamp_ms=1358137493000, 
              retweeted_count=100),
        Tweet(id=2, text="Daniel Day-Lewis takes home the award", 
              user=User(id=2, screen_name="user2"), timestamp_ms=1358137494000, 
              retweeted_count=50),
        Tweet(id=3, text="Hugh Jackman wins Best Actor!", 
              user=User(id=3, screen_name="user3"), timestamp_ms=1358137495000, 
              retweeted_count=200),
        Tweet(id=4, text="Hugh Jackman takes the award", 
              user=User(id=4, screen_name="user4"), timestamp_ms=1358137496000, 
              retweeted_count=75),
        Tweet(id=5, text="Bradley Cooper wins Best Actor!", 
              user=User(id=5, screen_name="user5"), timestamp_ms=1358137497000, 
              retweeted_count=10),
        Tweet(id=6, text="Daniel Day-Lewis is the winner", 
              user=User(id=6, screen_name="user6"), timestamp_ms=1358137498000, 
              retweeted_count=25),
    ]
    
    # Test different strategies
    strategies = [
        AggregationStrategy.MOST_FREQUENT,
        AggregationStrategy.LONGEST,
        AggregationStrategy.HIGHEST_RETWEET_COUNT,
        AggregationStrategy.COMBINED
    ]
    
    for strategy in strategies:
        print(f"\n--- {strategy.value.upper()} Strategy ---")
        
        # Create aggregator
        aggregator = AwardAggregator(strategy=strategy)
        
        # Add data to aggregator
        for tweet in mock_tweets:
            if "Daniel Day-Lewis" in tweet.text:
                aggregator.add_tweet_data(tweet, ["Daniel Day-Lewis"], "winners")
            elif "Hugh Jackman" in tweet.text:
                aggregator.add_tweet_data(tweet, ["Hugh Jackman"], "winners")
            elif "Bradley Cooper" in tweet.text:
                aggregator.add_tweet_data(tweet, ["Bradley Cooper"], "winners")
        
        # Get results
        top_candidates = aggregator.get_top_candidates(n=3)
        
        print("Top candidates:")
        for i, candidate in enumerate(top_candidates, 1):
            print(f"{i}. {candidate.name}")
            print(f"   Frequency: {candidate.frequency}")
            print(f"   Total Retweets: {candidate.total_retweets}")
            print(f"   Average Retweets: {candidate.avg_retweets:.1f}")
            print(f"   Length: {candidate.length}")
            print(f"   Score: {candidate.weighted_score:.3f}")
        
        # Get best single result
        best = aggregator.get_best_candidate()
        print(f"Best candidate: {best}")
        
        # Get statistics
        stats = aggregator.get_statistics()
        print(f"Total candidates: {stats['total_candidates']}")
        print(f"Total tweets: {stats['total_tweets']}")


if __name__ == "__main__":
    test_aggregation()
