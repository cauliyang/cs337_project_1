"""summary and extract award information from tweets after pre-processing"""

from collections import Counter
from pathlib import Path

from award.extractors.additional_goals_extractor import AdditionalGoalsExtractor
from award.extractors.award_extractor import AwardExtractor
from award.extractors.host_extractor import HostExtractor
from award.extractors.nominee_extractor import NomineeExtractor
from award.extractors.presenter_extractor import PresenterExtractor
from award.extractors.winner_extractor import WinnerExtractor
from award.processor import ProcessorPipeline
from award.processors.cleaner import (
    FtfyCleaner,
    UnidecodeCleaner,
    UrlCleaner,
    WhitespaceCollapseCleaner,
    normalize_text,
)
from award.processors.filter import EmptyTextFilter, GroupTweetsFilter, KeywordFilter
from award.read import TweetReader
from award.tweet import TweetListAdapter
from award.write import generate_outputs, get_top_candidates

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

    host_extractor = HostExtractor(min_mentions=30, top_n=2)
    # Use only host-related tweets for efficiency
    host_tweets = grouped_tweets.get("host", [])
    print(f"Using {len(host_tweets)} host-related tweets")
    hosts = host_extractor.extract(host_tweets)
    print(f"✓ Extracted {len(hosts)} hosts: {hosts}")

    # Step 4: Extract awards using AwardExtractor with POS-detected mentions
    print("\n" + "-" * 60)
    print("PHASE 2: Award Discovery")
    print("-" * 60)

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

    # Step 4b: Use hardcoded template awards for extraction
    print("\n" + "-" * 60)
    print("PHASE 2b: Template Awards")
    print("-" * 60)

    # Use hardcoded template awards to avoid cascade errors
    template_awards = AWARD_NAMES
    print(f"✓ Using {len(template_awards)} hardcoded template awards for extraction")
    print("   (Templates ensure accurate winner/nominee/presenter extraction)")
    print(f"  (POS-discovered awards: {len(discovered_awards)} will be used for 'awards' field)")
    
    # Create mapping from template awards to discovered variants
    # This allows matching using both template names AND discovered variants
    award_variants_map = {}
    
    for template_award in template_awards:
        template_words = set(normalize_text(template_award).split())
        matching_discovered = []
        
        for discovered_award in discovered_awards:
            discovered_words = set(normalize_text(discovered_award).split())
            overlap = len(template_words & discovered_words)
            overlap_ratio = overlap / len(template_words) if template_words else 0
            
            if overlap_ratio >= 0.7:
                matching_discovered.append(discovered_award)
        
        variants = (
            [normalize_text(template_award)] + 
            [normalize_text(v) for v in matching_discovered]
        )
        award_variants_map[template_award] = list(set(variants))
        
        if len(variants) > 1:
            print(f"  {template_award}: {len(variants)} variants")

    # Step 5: Extract winners (using template awards to avoid cascade errors)
    print("\n" + "-" * 60)
    print("PHASE 3: Winner Extraction")
    print("-" * 60)

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

    # Step 6: Extract nominees (using nominee-related tweets)
    print("\n" + "-" * 60)
    print("PHASE 4: Nominee Extraction")
    print("-" * 60)

        nominee_extractor = NomineeExtractor(min_mentions=3, top_n=5)
        # Use nominee tweets AND win tweets for better coverage
        nominee_tweets = grouped_tweets.get("nominee", [])
        win_tweets = grouped_tweets.get("win", [])
        combined_tweets = nominee_tweets + win_tweets[:1000]  # Limit win tweets
        print(f"Using {len(combined_tweets)} tweets for nominee extraction ({len(nominee_tweets)} nominee-related, {len(win_tweets)} win-related)")

        # Pass POS-detected award mentions and winners
        tweet_awards = group_filter.tweet_awards
        
        # Extract nominees using the regular extract method
        nominees = nominee_extractor.extract(combined_tweets, template_awards, winners, tweet_awards)

    # Count how many awards have nominees
    nominees_found = sum(1 for n in nominees.values() if n)
    print(f"✓ Extracted nominees for {nominees_found}/{len(template_awards)} awards")

    # Step 7: Extract presenters (using presenter-related tweets)
    print("\n" + "-" * 60)
    print("PHASE 5: Presenter Extraction")
    print("-" * 60)

    presenter_extractor = PresenterExtractor(min_mentions=3, top_n=2)
    # Use only presenter-related tweets for efficiency
    presenter_tweets = grouped_tweets.get("presenter", [])
    print(f"Using {len(presenter_tweets)} presenter-related tweets")

    # Pass POS-detected award mentions
    presenters = presenter_extractor.extract(presenter_tweets, template_awards, tweet_awards)

    # Count how many awards have presenters
    presenters_found = sum(1 for p in presenters.values() if p)
    print(f"✓ Extracted presenters for {presenters_found}/{len(template_awards)} awards")

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

    additional_extractor = AdditionalGoalsExtractor(min_mentions=5)
    # Use all tweets for additional goals detection
    additional_goals = additional_extractor.extract(all_tweets)
    print(f"✓ Extracted {len(additional_goals)} additional goals")

    # Step 10: Extract candidate lists from Counters
    print("\n" + "-" * 60)
    print("PHASE 8: Candidate Extraction")
    print("-" * 60)

    # Extract host candidates (top 10)
    host_candidates = get_top_candidates(host_extractor.person_counts, max_size=10) if hosts else []
    print(f"✓ Extracted {len(host_candidates)} host candidates")

    # Extract award candidates for each award
    award_candidates = {}
    for award in template_awards:
        # Get Counters from extractors
        winner_counter = winner_extractor.award_winner_counters.get(award, Counter())
        nominee_counter = nominee_extractor.award_nominee_counters.get(award, Counter())
        presenter_counter = presenter_extractor.award_presenter_counters.get(award, Counter())

        award_candidates[award] = {
            "winner_candidates": get_top_candidates(winner_counter, max_size=10),
            "nominee_candidates": get_top_candidates(nominee_counter, max_size=20),
            "presenters_candidates": get_top_candidates(presenter_counter, max_size=10),
        }

    print(f"✓ Extracted candidates for {len(award_candidates)} awards")

    # Extract additional goals candidates (top 5 for each goal)
    additional_goals_candidates = {}
    if additional_goals:
        for goal_key in additional_extractor.goal_counters.keys():
            goal_counter = additional_extractor.goal_counters[goal_key]
            additional_goals_candidates[goal_key] = get_top_candidates(goal_counter, max_size=5)

    print(f"✓ Extracted candidates for {len(additional_goals_candidates)} additional goals")

    # Step 11: Generate outputs
    print("\n" + "-" * 60)
    print("PHASE 9: Output Generation")
    print("-" * 60)

    # Output: Use discovered_awards for "awards" field, but award_data uses template_awards
    # The "awards" list shows what we discovered, award_data contains all 26 template awards
    json_path, text_path = generate_outputs(
        hosts=hosts,
        awards=discovered_awards,  # Use discovered awards for the awards list
        award_data=award_data,  # Use template-based award_data (all 26 awards)
        year=year,
        additional_goals=additional_goals,  # Add fun categories
        host_candidates=host_candidates,  # Add host candidates
        award_candidates=award_candidates,  # Add award candidates
        additional_goals_candidates=additional_goals_candidates,  # Add additional goal candidates
    )

    print(f"✓ JSON output: {json_path}")
    print(f"✓ Text output: {text_path}")

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
