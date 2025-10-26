"""summary and extract award information from tweets after pre-processing"""

from pathlib import Path

from award.processor import ProcessorPipeline
from award.processors.cleaner import FtfyCleaner, UnidecodeCleaner, UrlCleaner, WhitespaceCollapseCleaner
from award.processors.filter import EmptyTextFilter, GroupTweetsFilter, KeywordFilter
from award.read import TweetReader
from award.tweet import TweetListAdapter

# Global variable for template award names (hardcoded to avoid cascading errors)
# These are the official Golden Globes 2013 award categories
# Used for extracting winners, nominees, and presenters
AWARD_NAMES = [
    "best screenplay - motion picture",
    "best director - motion picture",
    "best performance by an actress in a television series - comedy or musical",
    "best foreign language film",
    "best performance by an actor in a supporting role in a motion picture",
    "best performance by an actress in a supporting role in a series, mini-series or motion picture made for television",  # noqa: E501
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


def main(input_file: Path, year: str, *, save_grouped_tweets: bool = False):
    # Create text cleaning pipeline
    text_pipeline = ProcessorPipeline(
        [
            FtfyCleaner(),
            UrlCleaner(),
            UnidecodeCleaner(),
            WhitespaceCollapseCleaner(),
            EmptyTextFilter(),
        ]
    )

    # Create grouping pipeline
    group_filter = GroupTweetsFilter()
    group_pipeline = ProcessorPipeline(
        [
            KeywordFilter(keywords=["RT"], case_sensitive=True),  # Filter out retweets
            group_filter,
        ]
    )

    # Combine pipelines: group first, then clean
    tweet_reader = TweetReader(
        input_file,
        pipeline=group_pipeline + text_pipeline,
        log=False,  # Disable verbose logging
    )

    # Extract and collect all tweets
    all_tweets = list(tweet_reader.read())
    print(f"✓ Loaded, filtered and processed {len(all_tweets)} tweets")

    # Get grouped tweets
    grouped_tweets = group_filter.groups
    print(f"✓ Tweets grouped into {len(grouped_tweets)} categories:")
    for group, tweets in grouped_tweets.items():
        print(f"  - {group}: {len(tweets)} tweets")

    if save_grouped_tweets:
        for group, tweets in grouped_tweets.items():
            with open(f"data/gg{year}_{group}.json", "wb") as f:
                json_data = TweetListAdapter.dump_json(tweets)
                f.write(json_data)

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

    # Step 4: Extract awards using AwardExtractor with POS-detected mentions
    print("\n" + "-" * 60)
    print("PHASE 2: Award Discovery")
    print("-" * 60)

    try:
        from award.extractors.award_extractor import AwardExtractor

        # Get POS-detected award mentions from GroupTweetsFilter
        tweet_awards = group_filter.tweet_awards

        # Use AwardExtractor with POS-detected awards for consistency
        award_extractor = AwardExtractor(min_mentions=5, cluster_threshold=0.85, expected_count=26)
        win_tweets = grouped_tweets.get("win", [])

        # Pass tweet_awards for better clustering and canonicalization
        discovered_awards = award_extractor.extract(win_tweets, tweet_awards)

        print(f"✓ Discovered {len(discovered_awards)} awards")
        if discovered_awards:
            print(f"Sample awards: {discovered_awards[:5]}")

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
    print(f"✓ Using {len(template_awards)} hardcoded template awards for extraction")
    print("   (Templates ensure accurate winner/nominee/presenter extraction)")
    print(f"  (POS-discovered awards: {len(discovered_awards)} will be used for 'awards' field)")

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
        winners = winner_extractor.extract(win_tweets, template_awards, tweet_awards, hosts=hosts)

        # Count how many winners found
        winners_found = sum(1 for w in winners.values() if w)
        print(f"✓ Extracted winners for {winners_found}/{len(template_awards)} awards")
    except Exception as e:
        print(f"✗ Error extracting winners: {e}")
        import traceback

        traceback.print_exc()
        winners = {award: "" for award in template_awards}

    # Step 6: Extract nominees (using nominee-related tweets)
    print("\n" + "-" * 60)
    print("PHASE 4: Nominee Extraction")
    print("-" * 60)

    try:
        from award.extractors.nominee_extractor import NomineeExtractor

        nominee_extractor = NomineeExtractor(min_mentions=3, top_n=5)
        # Use only nominee-related tweets for efficiency
        nominee_tweets = grouped_tweets.get("nominee", [])
        print(f"Using {len(nominee_tweets)} nominee-related tweets")

        # Pass POS-detected award mentions and winners
        tweet_awards = group_filter.tweet_awards
        nominees = nominee_extractor.extract(nominee_tweets, template_awards, winners, tweet_awards)

        # Count how many awards have nominees
        nominees_found = sum(1 for n in nominees.values() if n)
        print(f"✓ Extracted nominees for {nominees_found}/{len(template_awards)} awards")
    except Exception as e:
        print(f"✗ Error extracting nominees: {e}")
        import traceback

        traceback.print_exc()
        nominees = {award: [] for award in template_awards}

    # Step 7: Extract presenters (using presenter-related tweets)
    print("\n" + "-" * 60)
    print("PHASE 5: Presenter Extraction")
    print("-" * 60)

    try:
        from award.extractors.presenter_extractor import PresenterExtractor

        presenter_extractor = PresenterExtractor(min_mentions=3, top_n=2)
        # Use only presenter-related tweets for efficiency
        presenter_tweets = grouped_tweets.get("presenter", [])
        print(f"Using {len(presenter_tweets)} presenter-related tweets")

        # Pass POS-detected award mentions
        presenters = presenter_extractor.extract(presenter_tweets, template_awards, tweet_awards)

        # Count how many awards have presenters
        presenters_found = sum(1 for p in presenters.values() if p)
        print(f"✓ Extracted presenters for {presenters_found}/{len(template_awards)} awards")
    except Exception as e:
        print(f"✗ Error extracting presenters: {e}")
        import traceback

        traceback.print_exc()
        presenters = {award: [] for award in template_awards}

    # Step 8: Build award_data structure (using template awards)
    print("\n" + "-" * 60)
    print("PHASE 6: Building Award Data")
    print("-" * 60)

    # Build award_data using TEMPLATE awards with all extracted data
    award_data = {}
    for award in template_awards:
        award_data[award] = {
            "presenters": presenters.get(award, []),
            "nominees": nominees.get(award, []),
            "winner": winners.get(award, ""),
        }
    print(f"✓ Built award_data for {len(award_data)} template awards")
    print(f"   Winners: {sum(1 for a in award_data.values() if a['winner'])}/{len(award_data)}")
    print(f"   Nominees: {sum(1 for a in award_data.values() if a['nominees'])}/{len(award_data)}")
    print(f"   Presenters: {sum(1 for a in award_data.values() if a['presenters'])}/{len(award_data)}")

    # Step 9: Extract additional goals (fun categories)
    print("\n" + "-" * 60)
    print("PHASE 7: Additional Goals Extraction")
    print("-" * 60)

    try:
        from award.extractors.additional_goals_extractor import AdditionalGoalsExtractor

        additional_extractor = AdditionalGoalsExtractor(min_mentions=5)
        # Use all tweets for additional goals detection
        additional_goals = additional_extractor.extract(all_tweets)
        print(f"✓ Extracted {len(additional_goals)} additional goals")
    except Exception as e:
        print(f"✗ Error extracting additional goals: {e}")
        import traceback

        traceback.print_exc()
        additional_goals = {}

    # Step 10: Generate outputs
    print("\n" + "-" * 60)
    print("PHASE 8: Output Generation")
    print("-" * 60)

    try:
        from award.write import generate_outputs

        # Output: discovered_awards for "awards" field, template awards for award_data
        json_path, text_path = generate_outputs(
            hosts=hosts,
            awards=discovered_awards,  # Use discovered awards for the awards list
            award_data=award_data,  # Use template-based award_data
            year=year,
            additional_goals=additional_goals,  # Add fun categories
        )

        print(f"✓ JSON output: {json_path}")
        print(f"✓ Text output: {text_path}")

    except Exception as e:
        print(f"✗ Error generating outputs: {e}")
        import traceback

        traceback.print_exc()
        return

    # Step 11: Summary
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Hosts: {len(hosts)}")
    print(f"Discovered Awards: {len(discovered_awards)}")
    print(f"Template Awards (for extraction): {len(template_awards)}")
    print(f"Additional Goals: {len(additional_goals)}")
    print(f"Results saved to: gg{year}_results.json")
    print("=" * 60)
