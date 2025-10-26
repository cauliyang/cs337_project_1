"""Error analysis utilities for extraction gap identification.

This module provides tools to analyze extraction failures by:
1. Finding tweets containing correct answers that were missed
2. Identifying patterns that current extraction logic fails to capture
3. Calculating extraction recall metrics

Used during development to iteratively improve extraction accuracy.
"""

import json
from pathlib import Path

from award.models import Tweet
from award.processors.cleaner import normalize_text


def load_ground_truth(year: str = "2013") -> dict:
    """Load correct answers from ground truth file.

    Args:
        year: Golden Globes year (e.g., "2013", "2015")

    Returns:
        Dictionary mapping award names to their correct winners, nominees, presenters

    Raises:
        FileNotFoundError: If ground truth file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    answers_file = Path(f"gg{year}answers.json")
    if not answers_file.exists():
        raise FileNotFoundError(f"Ground truth file not found: {answers_file}")

    with open(answers_file) as f:
        return json.load(f)


def find_tweets_with_answer(tweets: list[Tweet], answer: str, award: str) -> list[Tweet]:
    """Find tweets containing correct answer and award mention.

    Used to identify tweets that should have been captured by extraction logic
    but were missed. Helps discover patterns and signals current logic doesn't capture.

    Args:
        tweets: All tweets for this category (winner/nominee/presenter)
        answer: Correct answer from ground truth (e.g., "daniel day lewis")
        award: Award name to filter relevant tweets

    Returns:
        List of tweets mentioning both answer and award (normalized matching)

    Example:
        >>> tweets = load_tweets("data/gg2013.json")
        >>> win_tweets = filter_tweets(tweets, "win")
        >>> relevant = find_tweets_with_answer(
        ...     win_tweets,
        ...     "daniel day lewis",
        ...     "best performance by an actor in a motion picture - drama"
        ... )
        >>> print(f"Found {len(relevant)} tweets with correct answer")
    """
    normalized_answer = normalize_text(answer)
    normalized_award = normalize_text(award)

    matching = []
    for tweet in tweets:
        text = normalize_text(tweet.text)
        # Check if both answer and award are mentioned in the tweet
        if normalized_answer in text and normalized_award in text:
            matching.append(tweet)

    return matching


def analyze_pattern_gaps(tweets: list[Tweet], current_patterns: list) -> list[str]:
    """Analyze tweets to identify patterns current extractors miss.

    This is a manual inspection helper - prints sample tweets for human review
    to identify common phrases not captured by current regex patterns.

    Args:
        tweets: Tweets containing correct answer (from find_tweets_with_answer)
        current_patterns: Existing regex patterns used in extractor

    Returns:
        Empty list (patterns identified manually through inspection)

    Example:
        >>> # After finding relevant tweets
        >>> gaps = analyze_pattern_gaps(relevant, NOMINEE_PATTERNS)
        # Prints sample tweets for manual review
        # Developer identifies "in contention for" pattern not in current list
    """
    print(f"\n=== Analyzing {len(tweets)} tweets for pattern gaps ===")
    print("Current patterns:")
    for i, pattern in enumerate(current_patterns, 1):
        print(f"  {i}. {pattern.pattern if hasattr(pattern, 'pattern') else pattern}")

    print("\nSample tweets (first 10):")
    for i, tweet in enumerate(tweets[:10], 1):
        print(f"{i}. {tweet.text}")

    print("\nManual analysis required:")
    print("1. Review sample tweets above")
    print("2. Identify common phrases/patterns not captured by current patterns")
    print("3. Document new patterns in research.md")
    print("4. Add patterns to extractor pattern lists")

    return []  # To be filled manually after inspection


def calculate_extraction_recall(extracted: list[str], correct: list[str]) -> float:
    """Calculate recall: percentage of correct answers that were extracted.

    Recall = (Correct answers found) / (Total correct answers)

    Args:
        extracted: List of extracted entities (e.g., winner candidates)
        correct: List of correct entities from ground truth

    Returns:
        Recall score (0.0 to 1.0)

    Example:
        >>> extracted_nominees = ["argo", "django unchained", "life of pi"]
        >>> correct_nominees = ["lincoln", "django unchained", "life of pi", "argo", "zero dark thirty"]
        >>> recall = calculate_extraction_recall(extracted_nominees, correct_nominees)
        >>> print(f"Recall: {recall:.1%}")  # Output: "Recall: 60.0%"
    """
    if not correct:
        return 1.0  # No correct answers to find, trivially perfect

    # Normalize both lists for comparison
    normalized_extracted = {normalize_text(e) for e in extracted if e}
    normalized_correct = {normalize_text(c) for c in correct if c}

    # Count matches
    matches = normalized_extracted & normalized_correct
    recall = len(matches) / len(normalized_correct)

    return recall
