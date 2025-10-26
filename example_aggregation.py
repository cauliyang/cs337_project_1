#!/usr/bin/env python3
"""
Example script demonstrating how to use the aggregation feature.

This script shows how to:
1. Extract data from tweets using existing processors
2. Aggregate multiple candidate names
3. Select the most probable final answer using different strategies
"""

from src.award.extract import Extractor
from src.award.processor import ProcessorPipeline
from src.award.aggregate import AwardAggregator, MultiTypeAggregator, AggregationStrategy
from src.award.processors import (
    FtfyCleaner, UnidecodeCleaner, LanguageFilter, 
    AwardNameExtractor, NomineeExtractor, HostExtractor
)


def example_single_type_aggregation():
    """Example of aggregating a single type of extracted data."""
    print("=== Single Type Aggregation Example ===")
    
    # Create extractor with processors
    extractor = Extractor(
        "data/gg2013.json.zip",
        pipeline=ProcessorPipeline([
            FtfyCleaner(),
            UnidecodeCleaner(),
            LanguageFilter(),
            AwardNameExtractor(),
        ])
    )
    
    # Create aggregator for award names
    aggregator = AwardAggregator(strategy=AggregationStrategy.COMBINED)
    
    # Process tweets and aggregate results
    tweet_count = 0
    for tweet in extractor.extract():
        if hasattr(tweet, 'extracted_awards') and tweet.extracted_awards:
            aggregator.add_tweet_data(tweet, tweet.extracted_awards, "awards")
            tweet_count += 1
        
        # Limit processing for demo
        if tweet_count >= 1000:
            break
    
    print(f"Processed {tweet_count} tweets with award extractions")
    
    # Get results using different strategies
    strategies = [
        AggregationStrategy.MOST_FREQUENT,
        AggregationStrategy.LONGEST,
        AggregationStrategy.HIGHEST_RETWEET_COUNT,
        AggregationStrategy.COMBINED
    ]
    
    for strategy in strategies:
        aggregator.strategy = strategy
        top_candidates = aggregator.get_top_candidates(n=5, min_frequency=2)
        
        print(f"\n--- {strategy.value.upper()} Strategy ---")
        for i, candidate in enumerate(top_candidates, 1):
            print(f"{i}. {candidate.name}")
            print(f"   Frequency: {candidate.frequency}")
            print(f"   Total Retweets: {candidate.total_retweets}")
            print(f"   Length: {candidate.length}")
            print(f"   Score: {candidate.weighted_score:.3f}")
    
    # Get statistics
    stats = aggregator.get_statistics()
    print(f"\n--- Statistics ---")
    print(f"Total candidates: {stats['total_candidates']}")
    print(f"Total tweets: {stats['total_tweets']}")
    print(f"Total retweets: {stats['total_retweets']}")


def example_multi_type_aggregation():
    """Example of aggregating multiple types of extracted data."""
    print("\n=== Multi-Type Aggregation Example ===")
    
    # Create extractor with multiple processors
    extractor = Extractor(
        "data/gg2013.json.zip",
        pipeline=ProcessorPipeline([
            FtfyCleaner(),
            UnidecodeCleaner(),
            LanguageFilter(),
            AwardNameExtractor(),
            NomineeExtractor(),
            HostExtractor(),
        ])
    )
    
    # Create multi-type aggregator
    multi_aggregator = MultiTypeAggregator(strategy=AggregationStrategy.COMBINED)
    
    # Process tweets and aggregate results
    tweet_count = 0
    for tweet in extractor.extract():
        extracted_data = {}
        
        # Collect all extracted data
        if hasattr(tweet, 'extracted_awards') and tweet.extracted_awards:
            extracted_data['awards'] = tweet.extracted_awards
        
        if hasattr(tweet, 'extracted_nominees') and tweet.extracted_nominees:
            extracted_data['nominees'] = tweet.extracted_nominees
        
        if hasattr(tweet, 'extracted_winners') and tweet.extracted_winners:
            extracted_data['winners'] = tweet.extracted_winners
        
        if hasattr(tweet, 'extracted_hosts') and tweet.extracted_hosts:
            extracted_data['hosts'] = tweet.extracted_hosts
        
        if extracted_data:
            multi_aggregator.add_tweet_data(tweet, extracted_data)
            tweet_count += 1
        
        # Limit processing for demo
        if tweet_count >= 500:
            break
    
    print(f"Processed {tweet_count} tweets with extractions")
    
    # Get results for each type
    results = multi_aggregator.get_results(min_frequency=2)
    
    for item_type, candidates in results.items():
        print(f"\n--- Top {item_type.upper()} ---")
        for i, candidate in enumerate(candidates[:5], 1):
            print(f"{i}. {candidate}")
    
    # Get single best results
    single_results = multi_aggregator.get_single_results(min_frequency=2)
    print(f"\n--- Best Single Results ---")
    for item_type, best_candidate in single_results.items():
        print(f"{item_type}: {best_candidate}")


def example_custom_aggregation():
    """Example of custom aggregation with specific criteria."""
    print("\n=== Custom Aggregation Example ===")
    
    # Create a custom aggregator that prioritizes retweets
    aggregator = AwardAggregator(strategy=AggregationStrategy.HIGHEST_RETWEET_COUNT)
    
    # Simulate some extracted data with different retweet counts
    from src.award.tweet import Tweet, User
    
    # Create mock tweets with different retweet counts
    mock_tweets = [
        Tweet(id=1, text="Best Actor - Daniel Day-Lewis wins!", user=User(id=1, screen_name="user1"), timestamp_ms=1358137493000, retweeted_count=100),
        Tweet(id=2, text="Best Actor - Daniel Day-Lewis takes home the award", user=User(id=2, screen_name="user2"), timestamp_ms=1358137494000, retweeted_count=50),
        Tweet(id=3, text="Best Actor - Hugh Jackman wins!", user=User(id=3, screen_name="user3"), timestamp_ms=1358137495000, retweeted_count=200),
        Tweet(id=4, text="Best Actor - Hugh Jackman takes the award", user=User(id=4, screen_name="user4"), timestamp_ms=1358137496000, retweeted_count=75),
        Tweet(id=5, text="Best Actor - Bradley Cooper wins!", user=User(id=5, screen_name="user5"), timestamp_ms=1358137497000, retweeted_count=10),
    ]
    
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
    
    print("Top candidates by retweet count:")
    for i, candidate in enumerate(top_candidates, 1):
        print(f"{i}. {candidate.name}")
        print(f"   Frequency: {candidate.frequency}")
        print(f"   Total Retweets: {candidate.total_retweets}")
        print(f"   Average Retweets: {candidate.avg_retweets:.1f}")


if __name__ == "__main__":
    print("Award Extraction Aggregation Examples")
    print("=" * 50)
    
    try:
        # Run examples
        example_single_type_aggregation()
        example_multi_type_aggregation()
        example_custom_aggregation()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure you have the required data file and dependencies installed.")
