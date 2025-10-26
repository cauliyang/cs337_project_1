#!/usr/bin/env python3
"""
Example usage of the enhanced extraction processors for Golden Globes tweets.

This script demonstrates how to use the various extractors to extract
award-related information from tweets.
"""

from src.award.extract import Extractor
from src.award.processors import (
    AwardNameExtractor,
    NomineeExtractor,
    HostExtractor,
    PresenterExtractor,
    SpeechExtractor,
    FashionExtractor,
)


def main():
    """Demonstrate the extraction capabilities."""
    
    # Create a pipeline with all the extractors
    pipeline = Extractor(
        "data/gg2013.json.zip",
        processors=[
            AwardNameExtractor(),
            NomineeExtractor(),
            HostExtractor(),
            PresenterExtractor(),
            SpeechExtractor(),
            FashionExtractor(),
        ]
    )
    
    print("Extracting award-related information from Golden Globes tweets...")
    print("=" * 60)
    
    # Process first 50 tweets as an example
    tweet_count = 0
    for tweet in pipeline.extract():
        if tweet_count >= 50:
            break
            
        print(f"\nTweet {tweet_count + 1}:")
        print(f"Text: {tweet.text[:100]}...")
        
        # Display extracted information
        if hasattr(tweet, 'extracted_awards') and tweet.extracted_awards:
            print(f"Awards: {tweet.extracted_awards}")
            
        if hasattr(tweet, 'extracted_winners') and tweet.extracted_winners:
            print(f"Winners: {tweet.extracted_winners}")
            
        if hasattr(tweet, 'extracted_nominees') and tweet.extracted_nominees:
            print(f"Nominees: {tweet.extracted_nominees}")
            
        if hasattr(tweet, 'extracted_hosts') and tweet.extracted_hosts:
            print(f"Hosts: {tweet.extracted_hosts}")
            
        if hasattr(tweet, 'extracted_presenters') and tweet.extracted_presenters:
            print(f"Presenters: {tweet.extracted_presenters}")
            
        if hasattr(tweet, 'extracted_quotes') and tweet.extracted_quotes:
            print(f"Quotes: {tweet.extracted_quotes}")
            
        if hasattr(tweet, 'fashion_descriptions') and tweet.fashion_descriptions:
            print(f"Fashion: {tweet.fashion_descriptions}")
            
        tweet_count += 1
    
    print(f"\nProcessed {tweet_count} tweets with extraction capabilities.")


if __name__ == "__main__":
    main()
