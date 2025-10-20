"""summary and extract award information from tweets after pre-processing"""

from pathlib import Path

from award.tweet import TweetListAdapter


def main(input_file: Path, output_file: Path):
    with open(
        input_file,
    ) as f:
        json_data = f.read()
    tweets = TweetListAdapter.validate_json(json_data)  # noqa: F841
    print(f"Total tweets for summary: {len(tweets)}")
