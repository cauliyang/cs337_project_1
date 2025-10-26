"""Version 0.5"""

import json
from pathlib import Path
from typing import Any

from rich import print

from award.cli import extract

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
            f"Results file gg{year}_results.json not found. Please run main() first to generate results."
        )

    with open(results_file, encoding="utf-8") as f:
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
    # New format: return top 2 hosts from host_candidates
    host_candidates = data.get("host_candidates", [])
    if len(host_candidates) >= 2:
        return host_candidates[:2]  # Return top 2 candidates as hosts
    elif len(host_candidates) == 1:
        return host_candidates
    elif data.get("host"):
        return [data["host"]]
    return []


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
    # New flat format: awards are top-level keys
    # Return all award keys (template awards), not just discovered awards from "awards" list
    award_keys = [k for k in data.keys() if isinstance(data.get(k), dict)]
    return {award: data.get(award, {}).get("nominees", []) for award in award_keys}


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
    # New flat format: awards are top-level keys
    # Return all award keys (template awards), not just discovered awards from "awards" list
    award_keys = [k for k in data.keys() if isinstance(data.get(k), dict)]
    return {award: data.get(award, {}).get("winner", "") for award in award_keys}


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
    # New flat format: awards are top-level keys
    # Return all award keys (template awards), not just discovered awards from "awards" list
    award_keys = [k for k in data.keys() if isinstance(data.get(k), dict)]
    return {award: data.get(award, {}).get("presenters", []) for award in award_keys}


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
    extract.main(input_file=Path("data/gg2013.json.zip"), year=YEAR)

    return


if __name__ == "__main__":
    main()
