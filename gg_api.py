"""Version 0.5"""

import json
from pathlib import Path
from typing import Any

# Year of the Golden Globes ceremony being analyzed
YEAR = "2013"

# Global variable for template award names (hardcoded to avoid cascading errors)
# These are the official Golden Globes 2013 award categories
# Used for extracting winners, nominees, and presenters
AWARD_NAMES = [
    "best screenplay - motion picture",
    "best director - motion picture",
    "best performance by an actress in a television series - comedy or musical",
    "best foreign language film",
    "best performance by an actor in a supporting role in a motion picture",
    "best performance by an actress in a supporting role in a series, mini-series or motion picture made for television",
    "best motion picture - comedy or musical",
    "best performance by an actress in a motion picture - comedy or musical",
    "best mini-series or motion picture made for television",
    "best original score - motion picture",
    "best performance by an actress in a television series - drama",
    "best performance by an actress in a motion picture - drama",
    "cecil b. demille award",
    "best performance by an actor in a motion picture - comedy or musical",
    "best motion picture - drama",
    "best performance by an actor in a supporting role in a series, mini-series or motion picture made for television",
    "best performance by an actress in a supporting role in a motion picture",
    "best television series - drama",
    "best performance by an actor in a mini-series or motion picture made for television",
    "best performance by an actress in a mini-series or motion picture made for television",
    "best animated feature film",
    "best original song - motion picture",
    "best performance by an actor in a motion picture - drama",
    "best television series - comedy or musical",
    "best performance by an actor in a television series - drama",
    "best performance by an actor in a television series - comedy or musical",
]

# Module-level cache for JSON results
_RESULTS_CACHE: dict[str, Any] = {}


def _load_results(year: str) -> dict:
    """
    Load results from JSON file with caching.

    Args:
        year: Year string (e.g., "2013")

    Returns:
        Dictionary with extraction results

    Raises:
        FileNotFoundError: If results file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    if year in _RESULTS_CACHE:
        return _RESULTS_CACHE[year]

    results_file = Path(f"gg{year}_results.json")
    if not results_file.exists():
        raise FileNotFoundError(
            f"Results file gg{year}_results.json not found. "
            f"Please run main() first to generate results."
        )

    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    _RESULTS_CACHE[year] = data
    return data


def get_hosts(year):
    """Returns the host(s) of the Golden Globes ceremony for the given year.

    Args:
        year (str): The year of the Golden Globes ceremony (e.g., "2013")

    Returns:
        list: A list of strings containing the host names.
              Example: ["Seth Meyers"] or ["Tina Fey", "Amy Poehler"]

    Note:
        - Do NOT change the name of this function or what it returns
        - The function should return a list even if there's only one host
    """
    data = _load_results(year)
    return data["hosts"]


def get_awards(year):
    """Returns the list of award categories for the Golden Globes ceremony.

    Args:
        year (str): The year of the Golden Globes ceremony (e.g., "2013")

    Returns:
        list: A list of strings containing award category names.
              Example: ["Best Motion Picture - Drama", "Best Motion Picture - Musical or Comedy",
                       "Best Performance by an Actor in a Motion Picture - Drama"]

    Note:
        - Do NOT change the name of this function or what it returns
        - Award names should be extracted from tweets, not hardcoded
        - The only hardcoded part allowed is the word "Best"
    """
    data = _load_results(year)
    return data["awards"]


def get_nominees(year):
    """Returns the nominees for each award category.

    Args:
        year (str): The year of the Golden Globes ceremony (e.g., "2013")

    Returns:
        dict: A dictionary where keys are award category names and values are
              lists of nominee strings.
              Example: {
                  "Best Motion Picture - Drama": [
                      "Three Billboards Outside Ebbing, Missouri",
                      "Call Me by Your Name",
                      "Dunkirk",
                      "The Post",
                      "The Shape of Water"
                  ],
                  "Best Motion Picture - Musical or Comedy": [
                      "Lady Bird",
                      "The Disaster Artist",
                      "Get Out",
                      "The Greatest Showman",
                      "I, Tonya"
                  ]
              }

    Note:
        - Do NOT change the name of this function or what it returns
        - Use the hardcoded award names as keys (from the global AWARD_NAMES list)
        - Each value should be a list of strings, even if there's only one nominee
    """
    data = _load_results(year)
    return {award: data["award_data"][award]["nominees"] for award in data["award_data"]}


def get_winner(year):
    """Returns the winner for each award category.

    Args:
        year (str): The year of the Golden Globes ceremony (e.g., "2013")

    Returns:
        dict: A dictionary where keys are award category names and values are
              single winner strings.
              Example: {
                  "Best Motion Picture - Drama": "Three Billboards Outside Ebbing, Missouri",
                  "Best Motion Picture - Musical or Comedy": "Lady Bird",
                  "Best Performance by an Actor in a Motion Picture - Drama": "Gary Oldman"
              }

    Note:
        - Do NOT change the name of this function or what it returns
        - Use the hardcoded award names as keys (from the global AWARD_NAMES list)
        - Each value should be a single string (the winner's name)
    """
    data = _load_results(year)
    return {award: data["award_data"][award]["winner"] for award in data["award_data"]}


def get_presenters(year):
    """Returns the presenters for each award category.

    Args:
        year (str): The year of the Golden Globes ceremony (e.g., "2013")

    Returns:
        dict: A dictionary where keys are award category names and values are
              lists of presenter strings.
              Example: {
                  "Best Motion Picture - Drama": ["Barbra Streisand"],
                  "Best Motion Picture - Musical or Comedy": ["Alicia Vikander", "Michael Keaton"],
                  "Best Performance by an Actor in a Motion Picture - Drama": ["Emma Stone"]
              }

    Note:
        - Do NOT change the name of this function or what it returns
        - Use the hardcoded award names as keys (from the global AWARD_NAMES list)
        - Each value should be a list of strings, even if there's only one presenter
    """
    data = _load_results(year)
    return {award: data["award_data"][award]["presenters"] for award in data["award_data"]}


def pre_ceremony():
    """Pre-processes and loads data for the Golden Globes analysis.

    This function should be called before any other functions to:
    - Load and process the tweet data from gg2013.json
    - Download required models (e.g., spaCy models)
    - Perform any initial data cleaning or preprocessing
    - Store processed data in files or database for later use

    This is the first function the TA will run when grading.

    Note:
        - Do NOT change the name of this function or what it returns
        - This function should handle all one-time setup tasks
        - Print progress messages to help with debugging
    """
    print("=" * 60)
    print("Pre-ceremony processing started...")
    print("=" * 60)

    # Verify spaCy model is installed
    try:
        from award.nlp import get_nlp
        nlp = get_nlp()
        print(f"✓ spaCy model loaded: {nlp.meta['name']}")
    except Exception as e:
        print(f"✗ Error loading spaCy model: {e}")
        print("Please install with: uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl")
        return

    # Verify tweet data exists
    tweet_file = Path("data/gg2013.json")
    if not tweet_file.exists():
        # Check for zip file
        zip_file = Path("data/gg2013.json.zip")
        if zip_file.exists():
            print(f"✓ Tweet data found (compressed): {zip_file}")
        else:
            print(f"✗ Tweet data not found: {tweet_file}")
            return
    else:
        print(f"✓ Tweet data found: {tweet_file}")

    print("=" * 60)
    print("Pre-ceremony processing complete.")
    print("=" * 60)
    return


def main():
    """Main function that orchestrates the Golden Globes analysis.

    This function should:
    - Call pre_ceremony() to set up the environment
    - Run the main analysis pipeline
    - Generate and save results in the required JSON format
    - Print progress messages and final results

    Usage:
        - Command line: python gg_api.py
        - Python interpreter: import gg_api; gg_api.main()

    This is the second function the TA will run when grading.

    Note:
        - Do NOT change the name of this function or what it returns
        - This function should coordinate all the analysis steps
        - Make sure to handle errors gracefully
    """
    print("\n" + "=" * 60)
    print("Golden Globes 2013 - Extraction Pipeline")
    print("=" * 60)

    # Step 1: Pre-ceremony setup
    pre_ceremony()

    # Step 2: Load and group tweets
    print("\nLoading and grouping tweets...")
    from award.extract import Extractor
    from award.processors.filter import EmptyTextFilter, KeywordFilter, GroupTweetsFilter
    from award.processors.cleaner import FtfyCleaner, UnidecodeCleaner, UrlCleaner, SpaceCombinationCleaner
    from award.processor import ProcessorPipeline

    try:
        # Create text cleaning pipeline
        text_pipeline = ProcessorPipeline([
            FtfyCleaner(),
            UrlCleaner(),
            UnidecodeCleaner(),
            SpaceCombinationCleaner(),
            EmptyTextFilter(),
        ])

        # Create grouping pipeline
        group_filter = GroupTweetsFilter()
        group_pipeline = ProcessorPipeline([
            KeywordFilter(keywords=["RT"], case_sensitive=True),  # Filter out retweets
            group_filter
        ])

        # Combine pipelines: group first, then clean
        extractor = Extractor(
            "data/gg2013.json",
            pipeline=group_pipeline + text_pipeline,
            log=False  # Disable verbose logging
        )

        # Extract and collect all tweets
        all_tweets = list(extractor.extract())
        print(f"✓ Loaded and processed {len(all_tweets)} tweets")

        # Get grouped tweets
        grouped_tweets = group_filter.groups
        print(f"✓ Tweets grouped into {len(grouped_tweets)} categories:")
        for group, tweets in grouped_tweets.items():
            print(f"  - {group}: {len(tweets)} tweets")

    except Exception as e:
        print(f"✗ Error loading tweets: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Extract hosts (using host-specific tweets)
    print("\n" + "-" * 60)
    print("PHASE 1: Host Extraction")
    print("-" * 60)

    try:
        from award.extractors.host_extractor import HostExtractor
        host_extractor = HostExtractor(min_mentions=30, top_n=2)
        # Use only host-related tweets for efficiency
        host_tweets = grouped_tweets.get("host", [])
        print(f"Using {len(host_tweets)} host-related tweets")
        hosts = host_extractor.extract(host_tweets)
        print(f"✓ Extracted {len(hosts)} hosts: {hosts}")
    except Exception as e:
        print(f"✗ Error extracting hosts: {e}")
        import traceback
        traceback.print_exc()
        hosts = []

    # Step 4: Discover awards (using winner group tweets - they contain award mentions)
    print("\n" + "-" * 60)
    print("PHASE 2: Award Discovery")
    print("-" * 60)

    try:
        from award.extractors.award_extractor import AwardExtractor
        award_extractor = AwardExtractor(min_mentions=5, cluster_threshold=0.8)
        # Use winner tweets since they contain award mentions
        win_tweets = grouped_tweets.get("win", [])
        print(f"Using {len(win_tweets)} winner tweets for award extraction")
        discovered_awards = award_extractor.extract(win_tweets)
        print(f"✓ Discovered {len(discovered_awards)} awards")
        # Print first few for verification
        if discovered_awards:
            print(f"Sample awards: {discovered_awards[:5] if len(discovered_awards) >= 5 else discovered_awards}")
    except Exception as e:
        print(f"✗ Error discovering awards: {e}")
        import traceback
        traceback.print_exc()
        discovered_awards = []

    # Step 4b: Use hardcoded template awards for extraction
    print("\n" + "-" * 60)
    print("PHASE 2b: Template Awards")
    print("-" * 60)
    
    # Use hardcoded template awards to avoid cascade errors
    template_awards = AWARD_NAMES
    print(f"✓ Using {len(template_awards)} hardcoded template awards")
    print(f"  (Templates ensure accurate winner/nominee/presenter extraction)")
    print(f"  (Discovered awards: {len(discovered_awards)} will be used for 'awards' field)")

    # Step 5: Extract winners (using template awards to avoid cascade errors)
    print("\n" + "-" * 60)
    print("PHASE 3: Winner Extraction")
    print("-" * 60)

    try:
        from award.extractors.winner_extractor import WinnerExtractor
        winner_extractor = WinnerExtractor(min_mentions=3)
        # Use only win-related tweets for efficiency
        win_tweets = grouped_tweets.get("win", [])
        print(f"Using {len(win_tweets)} win-related tweets")
        
        # Pass POS-detected award mentions to improve matching
        tweet_awards = group_filter.tweet_awards
        print(f"POS-detected awards in {len(tweet_awards)} tweets")
        
        # Extract winners using TEMPLATE awards (not discovered awards)
        print(f"Using {len(template_awards)} template awards for extraction")
        winners = winner_extractor.extract(win_tweets, template_awards, tweet_awards)
        
        # Count how many winners found
        winners_found = sum(1 for w in winners.values() if w)
        print(f"✓ Extracted winners for {winners_found}/{len(template_awards)} awards")
    except Exception as e:
        print(f"✗ Error extracting winners: {e}")
        import traceback
        traceback.print_exc()
        winners = {award: "" for award in template_awards}

    # Step 6: Build award_data structure (using template awards)
    print("\n" + "-" * 60)
    print("PHASE 4: Building Award Data")
    print("-" * 60)

    # TODO: Implement nominee/presenter extraction
    # These will use grouped_tweets for efficiency:
    # - nominee_tweets = grouped_tweets.get("nominee", [])
    # - presenter_tweets = grouped_tweets.get("presenter", [])
    
    # Build award_data using TEMPLATE awards (not discovered awards)
    award_data = {}
    for award in template_awards:
        award_data[award] = {
            "presenters": [],
            "nominees": [],
            "winner": winners.get(award, "")
        }
    print(f"✓ Built award_data for {len(award_data)} template awards")
    print(f"   (Nominee/presenter extraction not yet implemented)")

    # Step 7: Generate outputs
    print("\n" + "-" * 60)
    print("PHASE 5: Output Generation")
    print("-" * 60)

    try:
        from award.write import generate_outputs

        # Output: discovered_awards for "awards" field, template awards for award_data
        json_path, text_path = generate_outputs(
            hosts=hosts,
            awards=discovered_awards,  # Use discovered awards for the awards list
            award_data=award_data,  # Use template-based award_data
            year=YEAR
        )

        print(f"✓ JSON output: {json_path}")
        print(f"✓ Text output: {text_path}")

    except Exception as e:
        print(f"✗ Error generating outputs: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 7: Summary
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Hosts: {len(hosts)}")
    print(f"Discovered Awards: {len(discovered_awards)}")
    print(f"Template Awards (for extraction): {len(template_awards)}")
    print(f"Results saved to: gg{YEAR}_results.json")
    print("=" * 60)

    return


if __name__ == "__main__":
    main()
