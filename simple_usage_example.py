#!/usr/bin/env python3
"""
Simple usage example showing how to use the aggregation feature
with the existing extraction pipeline.
"""

from src.award.aggregate import AwardAggregator, AggregationStrategy
from src.award.tweet import Tweet, User


def simple_aggregation_example():
    """
    Simple example showing how to use aggregation to select the best candidate
    from multiple extraction results.
    """
    print("Simple Aggregation Usage Example")
    print("=" * 40)
    
    # Simulate extraction results from multiple tweets
    # In a real scenario, these would come from your extractors
    extraction_results = [
        # Tweet 1: Multiple candidates extracted
        {
            "tweet": Tweet(id=1, text="Best Actor goes to Daniel Day-Lewis!", 
                          user=User(id=1, screen_name="user1"), 
                          timestamp_ms=1358137493000, retweeted_count=150),
            "extracted_winners": ["Daniel Day-Lewis", "Daniel Day Lewis", "Day-Lewis"]
        },
        # Tweet 2: Different candidates
        {
            "tweet": Tweet(id=2, text="Daniel Day-Lewis wins the award", 
                          user=User(id=2, screen_name="user2"), 
                          timestamp_ms=1358137494000, retweeted_count=75),
            "extracted_winners": ["Daniel Day-Lewis", "Daniel Day-Lewis"]
        },
        # Tweet 3: Another variation
        {
            "tweet": Tweet(id=3, text="Winner is Daniel Day Lewis", 
                          user=User(id=3, screen_name="user3"), 
                          timestamp_ms=1358137495000, retweeted_count=200),
            "extracted_winners": ["Daniel Day Lewis", "Daniel Lewis"]
        },
        # Tweet 4: Different winner
        {
            "tweet": Tweet(id=4, text="Hugh Jackman takes the award", 
                          user=User(id=4, screen_name="user4"), 
                          timestamp_ms=1358137496000, retweeted_count=50),
            "extracted_winners": ["Hugh Jackman", "Jackman"]
        }
    ]
    
    # Create aggregator
    aggregator = AwardAggregator(strategy=AggregationStrategy.COMBINED)
    
    # Add all extraction results to the aggregator
    for result in extraction_results:
        tweet = result["tweet"]
        extracted_winners = result["extracted_winners"]
        aggregator.add_tweet_data(tweet, extracted_winners, "winners")
    
    # Get the best candidate using different strategies
    print("\nTesting different aggregation strategies:")
    
    strategies = [
        AggregationStrategy.MOST_FREQUENT,
        AggregationStrategy.HIGHEST_RETWEET_COUNT,
        AggregationStrategy.COMBINED
    ]
    
    for strategy in strategies:
        aggregator.strategy = strategy
        best_candidate = aggregator.get_best_candidate(min_frequency=1)
        print(f"{strategy.value}: {best_candidate}")
    
    # Get top 3 candidates with detailed scores
    print("\nTop 3 candidates (COMBINED strategy):")
    aggregator.strategy = AggregationStrategy.COMBINED
    top_candidates = aggregator.get_top_candidates(n=3, min_frequency=1)
    
    for i, candidate in enumerate(top_candidates, 1):
        print(f"{i}. {candidate.name}")
        print(f"   Frequency: {candidate.frequency}")
        print(f"   Total Retweets: {candidate.total_retweets}")
        print(f"   Average Retweets: {candidate.avg_retweets:.1f}")
        print(f"   Score: {candidate.weighted_score:.3f}")
    
    # Show statistics
    stats = aggregator.get_statistics()
    print(f"\nStatistics:")
    print(f"Total candidates: {stats['total_candidates']}")
    print(f"Total tweets: {stats['total_tweets']}")
    print(f"Total retweets: {stats['total_retweets']}")
    
    # Show frequency distribution
    print(f"\nCandidate frequencies:")
    for name, freq in stats['candidate_frequencies'].items():
        print(f"  {name}: {freq}")


def demonstrate_selection_criteria():
    """
    Demonstrate how different selection criteria work.
    """
    print("\n" + "=" * 50)
    print("Demonstrating Selection Criteria")
    print("=" * 50)
    
    # Create test data with different characteristics
    test_data = [
        # Short name, high frequency, low retweets
        {"name": "Tom", "freq": 10, "retweets": 5},
        # Long name, low frequency, high retweets  
        {"name": "Christopher Nolan", "freq": 2, "retweets": 1000},
        # Medium name, medium frequency, medium retweets
        {"name": "Daniel Day-Lewis", "freq": 5, "retweets": 500},
    ]
    
    # Create aggregator and add test data
    aggregator = AwardAggregator()
    
    for i, data in enumerate(test_data):
        tweet = Tweet(
            id=i, 
            text=f"Winner: {data['name']}", 
            user=User(id=i, screen_name=f"user{i}"), 
            timestamp_ms=1358137493000 + i * 1000, 
            retweeted_count=data['retweets']
        )
        
        # Add multiple times to simulate frequency
        for _ in range(data['freq']):
            aggregator.add_tweet_data(tweet, [data['name']], "winners")
    
    # Test different strategies
    strategies = [
        (AggregationStrategy.MOST_FREQUENT, "Most Frequent"),
        (AggregationStrategy.LONGEST, "Longest Name"),
        (AggregationStrategy.HIGHEST_RETWEET_COUNT, "Highest Retweets"),
        (AggregationStrategy.COMBINED, "Combined Score")
    ]
    
    for strategy, description in strategies:
        aggregator.strategy = strategy
        best = aggregator.get_best_candidate()
        print(f"{description}: {best}")


if __name__ == "__main__":
    simple_aggregation_example()
    demonstrate_selection_criteria()

