#!/usr/bin/env python3
"""
Example usage of the enhanced extraction processors with file output.

This script demonstrates how to use the various extractors to extract
award-related information from tweets and save the results to files.
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
from src.award.write import ExtractionWriter


def main():
    """Demonstrate the extraction capabilities with file output."""
    
    print("Extracting award-related information from Golden Globes tweets...")
    print("=" * 60)
    
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
    
    # Initialize the writer
    writer = ExtractionWriter("extracted_output")
    
    # Process tweets and collect them
    tweets = []
    tweet_count = 0
    
    print("Processing tweets...")
    for tweet in pipeline.extract():
        if tweet_count >= 100:  # Process 100 tweets as example
            break
        tweets.append(tweet)
        tweet_count += 1
        
        if tweet_count % 20 == 0:
            print(f"Processed {tweet_count} tweets...")
    
    print(f"\nProcessed {tweet_count} tweets with extraction capabilities.")
    print("\nSaving extracted data to files...")
    
    # Write all extracted data to files
    output_files = writer.write_all(tweets, "golden_globes_2013")
    
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE - Files saved:")
    print("=" * 60)
    
    for data_type, file_path in output_files.items():
        print(f"{data_type.upper()}: {file_path}")
    
    print("\n" + "=" * 60)
    print("DIRECTORY STRUCTURE:")
    print("=" * 60)
    print("extracted_output/")
    print("├── complete/")
    print("│   └── golden_globes_2013_complete.json")
    print("├── awards/")
    print("│   └── golden_globes_2013_awards.csv")
    print("├── winners/")
    print("│   └── golden_globes_2013_winners.csv")
    print("├── nominees/")
    print("│   └── golden_globes_2013_nominees.csv")
    print("├── fashion/")
    print("│   └── golden_globes_2013_fashion.csv")
    print("└── golden_globes_2013_summary.json")
    
    print("\n" + "=" * 60)
    print("FILE CONTENTS:")
    print("=" * 60)
    print("• complete.json: Full tweets with all extracted metadata")
    print("• awards.csv: Extracted award names")
    print("• winners.csv: Extracted winner names")
    print("• nominees.csv: Extracted nominee names")
    print("• fashion.csv: Fashion descriptions, celebrities, brands, colors")
    print("• summary.json: Extraction statistics and rates")
    
    # Display some sample extractions
    print("\n" + "=" * 60)
    print("SAMPLE EXTRACTIONS:")
    print("=" * 60)
    
    sample_count = 0
    for tweet in tweets:
        has_extractions = (
            (hasattr(tweet, 'extracted_awards') and tweet.extracted_awards) or
            (hasattr(tweet, 'extracted_winners') and tweet.extracted_winners) or
            (hasattr(tweet, 'extracted_nominees') and tweet.extracted_nominees) or
            (hasattr(tweet, 'fashion_descriptions') and tweet.fashion_descriptions)
        )
        
        if has_extractions and sample_count < 5:
            print(f"\n[TWEET {sample_count + 1}]")
            print(f"Text: {tweet.text[:100]}...")
            
            if hasattr(tweet, 'extracted_awards') and tweet.extracted_awards:
                print(f"Awards: {tweet.extracted_awards}")
                
            if hasattr(tweet, 'extracted_winners') and tweet.extracted_winners:
                print(f"Winners: {tweet.extracted_winners}")
                
            if hasattr(tweet, 'extracted_nominees') and tweet.extracted_nominees:
                print(f"Nominees: {tweet.extracted_nominees}")
                
            if hasattr(tweet, 'fashion_descriptions') and tweet.fashion_descriptions:
                print(f"Fashion: {tweet.fashion_descriptions}")
            
            sample_count += 1
    
    print(f"\nExtraction complete! Check the 'extracted_output' directory for all files.")


if __name__ == "__main__":
    main()
