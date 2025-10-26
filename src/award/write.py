"""Output generation for Golden Globes extraction results."""

import json
from collections import Counter
from pathlib import Path
from typing import TypedDict


class AwardDataDict(TypedDict, total=False):
    """Type hint for award data dictionary with candidate lists."""

    presenters: list[str]
    presenters_candidates: list[str]
    nominees: list[str]
    nominee_candidates: list[str]
    winner: str
    winner_candidates: list[str]


def get_top_candidates(counter: Counter, max_size: int = 10) -> list[str]:
    """
    Extract top N candidates from Counter, maintaining rank order.

    Args:
        counter: Counter object with entity mention frequencies
        max_size: Maximum number of candidates to return (default: 10)

    Returns:
        List of candidate names in descending order by frequency

    Example:
        >>> counter = Counter({"tina fey": 450, "amy poehler": 445, "seth meyers": 20})
        >>> get_top_candidates(counter, max_size=3)
        ['tina fey', 'amy poehler', 'seth meyers']
    """
    return [entity for entity, count in counter.most_common(max_size)]


def write_json_output(results: dict, year: str, output_dir: str = ".") -> Path:
    """
    Write extraction results to JSON file in autograder-compatible format.

    Args:
        results: Dictionary with flat structure (awards as top-level keys)
                 Required keys: 'host', 'host_candidates', 'awards'
                 Award names as top-level keys with candidate fields
        year: Year string (e.g., "2013")
        output_dir: Directory to write output file (default: current directory)

    Returns:
        Path to the created JSON file

    Raises:
        ValueError: If results dictionary is missing required keys
    """
    # Validate required top-level keys for flat structure
    required_keys = {"host", "host_candidates", "awards"}
    if not required_keys.issubset(results.keys()):
        missing = required_keys - results.keys()
        raise ValueError(f"Results missing required keys: {missing}")

    # Validate that awards in the awards list exist as top-level keys (if they're present)
    # Note: The "awards" list is discovered awards, which may be a subset of all awards in the JSON
    for award in results["awards"]:
        if award in results and isinstance(results[award], dict):
            award_data = results[award]
            # Check for required candidate fields
            required_award_keys = {
                "presenters",
                "presenters_candidates",
                "nominees",
                "nominee_candidates",
                "winner",
                "winner_candidates",
            }
            if not required_award_keys.issubset(award_data.keys()):
                missing = required_award_keys - award_data.keys()
                raise ValueError(f"Award '{award}' missing required candidate keys: {missing}")

    # Create output file path
    output_path = Path(output_dir) / f"gg{year}_results.json"

    # Write JSON with proper formatting
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"JSON results written to {output_path}")
    return output_path


def write_text_output(results: dict, year: str, output_dir: str = ".") -> Path:
    """
    Write extraction results to human-readable text file.

    Args:
        results: Dictionary with flat structure
        year: Year string (e.g., "2013")
        output_dir: Directory to write output file (default: current directory)

    Returns:
        Path to the created text file

    Raises:
        ValueError: If results dictionary is missing required keys
    """
    # Build output content
    lines = []
    NOT_EXTRACTED = "UNKNOWN"

    # Header
    lines.append("=" * 60)
    lines.append(f"Golden Globes {year} - Extraction Results")
    lines.append("=" * 60)
    lines.append("")

    # Hosts section
    lines.append("HOST")
    lines.append("-" * 60)
    host = results.get("host", "")
    if host:
        for host_name in host:
            lines.append(f"{host_name.title()}")
    else:
        lines.append("(No host extracted)")

    lines.append("")
    lines.append("HOST CANDIDATES")
    lines.append("-" * 60)
    host_candidates = results.get("host_candidates", [])
    if host_candidates:
        for candidate in host_candidates:
            lines.append(f"- {candidate.title()}")
    else:
        lines.append("(No data)")

    lines.append("")

    # Awards & Winners
    lines.append("AWARDS & WINNERS")
    lines.append("-" * 60)

    # Show all awards that have data (template awards), not just discovered awards
    # Get all award keys (exclude standard keys and candidate keys)
    standard_keys = {"host", "host_candidates", "awards"}
    award_keys = [
        k
        for k in results.keys()
        if k not in standard_keys and not k.endswith("_candidates") and isinstance(results.get(k), dict)
    ]

    for award in award_keys:
        # Award data is at top level in flat format
        award_data = results.get(award, {})

        # Award name (title case)
        lines.append("")
        lines.append(award.title())

        # Winner
        winner = award_data.get("winner", "")
        if winner:
            lines.append(f"  Winner: {winner.title()}")
        else:
            lines.append(f"  Winner: ({NOT_EXTRACTED})")

        # Winner Candidates
        winner_candidates = award_data.get("winner_candidates", [])
        if winner_candidates:
            lines.append("  Winner Candidates:")
            for candidate in winner_candidates:
                lines.append(f"    - {candidate.title()}")

        # Nominees
        nominees = award_data.get("nominees", [])
        if nominees:
            lines.append("  Nominees:")
            for nominee in nominees:
                lines.append(f"    - {nominee.title()}")
        elif "cecil" not in award.lower():
            lines.append(f"  Nominees: ({NOT_EXTRACTED})")

        # Nominee Candidates
        nominee_candidates = award_data.get("nominee_candidates", [])
        if nominee_candidates:
            lines.append("  Nominee Candidates:")
            for candidate in nominee_candidates:
                lines.append(f"    - {candidate.title()}")

        # Presenters
        presenters = award_data.get("presenters", [])
        if presenters:
            lines.append("  Presenters:")
            for presenter in presenters:
                lines.append(f"    - {presenter.title()}")

        # Presenter Candidates
        presenters_candidates = award_data.get("presenters_candidates", [])
        if presenters_candidates:
            lines.append("  Presenters Candidates:")
            for candidate in presenters_candidates:
                lines.append(f"    - {candidate.title()}")

    # Additional Goals
    # In flat format, additional goals are top-level keys
    # We need to detect them by looking for keys that are not standard fields or awards
    standard_keys = {"host", "host_candidates", "awards"} | set(award_keys)
    goal_keys = [
        k
        for k in results.keys()
        if k not in standard_keys and not k.endswith("_candidates") and not isinstance(results.get(k), dict)
    ]

    if goal_keys:
        lines.append("")
        lines.append("")
        lines.append("ADDITIONAL GOALS (OPTIONAL)")
        lines.append("-" * 60)
        lines.append("")

        for goal_name in goal_keys:
            winner = results.get(goal_name, "")
            lines.append(f"{goal_name}:")
            if winner:
                lines.append(f"  Winner: {winner.title()}")

            # Check for candidates
            candidates_key = f"{goal_name}_candidates"
            if candidates_key in results:
                candidates = results[candidates_key]
                if candidates:
                    lines.append("  Candidates:")
                    for candidate in candidates:
                        lines.append(f"    - {candidate.title()}")

        lines.append("")

    # Create output file path
    output_path = Path(output_dir) / f"gg{year}_results.txt"

    # Write text file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Human-readable results written to {output_path}")
    return output_path


def build_json_output(
    hosts: list[str],
    awards: list[str],
    award_data: dict,
    additional_goals: dict[str, str] | None = None,
    host_candidates: list[str] | None = None,
    award_candidates: dict[str, dict[str, list[str]]] | None = None,
    additional_goals_candidates: dict[str, list[str]] | None = None,
) -> dict:
    """
    Build JSON output structure from extraction results with candidate lists.

    This function transforms the extraction results into the autograder-compatible
    flat JSON format where award names are top-level keys and candidate lists are
    included for all roles.

    Args:
        hosts: List of normalized host names
        awards: List of normalized award names
        award_data: Dictionary mapping award names to data (presenters, nominees, winner)
        additional_goals: Optional dict mapping goal names to winners
        host_candidates: Optional list of top host candidates (ranked by confidence)
        award_candidates: Optional dict mapping award names to candidate dicts
            Format: {award_name: {
                "presenters_candidates": [list],
                "nominee_candidates": [list],
                "winner_candidates": [list]
            }}
        additional_goals_candidates: Optional dict mapping goal names to candidate lists

    Returns:
        Dictionary with flat structure for JSON output (autograder-compatible)

    Note:
        - Uses singular "host" (not "hosts") per autograder requirements
        - Award names appear as top-level keys (flat structure, not nested)
        - Uses hardcoded AWARD_NAMES as keys, discovered awards in "awards" list
    """
    # Initialize result with required top-level fields
    result = {}

    # Singular "host" field (first host if multiple, empty string if none)
    result["host"] = hosts if hosts else ""
    result["host_candidates"] = host_candidates if host_candidates is not None else []

    # Awards list (dynamically discovered awards)
    result["awards"] = awards

    # Each award becomes a top-level key with its data
    for award_name, data in award_data.items():
        award_dict = {
            "presenters": data.get("presenters", []),
            "nominees": data.get("nominees", []),
            "winner": data.get("winner", ""),
        }

        # Add candidate fields if provided
        if award_candidates and award_name in award_candidates:
            candidates = award_candidates[award_name]
            award_dict["presenters_candidates"] = candidates.get("presenters_candidates", [])
            award_dict["nominee_candidates"] = candidates.get("nominee_candidates", [])
            award_dict["winner_candidates"] = candidates.get("winner_candidates", [])
        else:
            award_dict["presenters_candidates"] = []
            award_dict["nominee_candidates"] = []
            award_dict["winner_candidates"] = []

        result[award_name] = award_dict

    if additional_goals:
        for goal_name, winner in additional_goals.items():
            result[goal_name] = winner

            # Add candidate list if provided
            if additional_goals_candidates and goal_name in additional_goals_candidates:
                result[f"{goal_name}_candidates"] = additional_goals_candidates[goal_name]

    return result


def generate_outputs(
    hosts: list[str],
    awards: list[str],
    award_data: dict,
    year: str,
    output_dir: str = ".",
    additional_goals: dict[str, str] | None = None,
    host_candidates: list[str] | None = None,
    award_candidates: dict[str, dict[str, list[str]]] | None = None,
    additional_goals_candidates: dict[str, list[str]] | None = None,
) -> tuple[Path, Path]:
    """
    Generate both JSON and human-readable output files with candidate lists.

    Args:
        hosts: List of normalized host names
        awards: List of normalized award names
        award_data: Dictionary mapping award names to data
        year: Year string (e.g., "2013")
        output_dir: Directory to write output files (default: current directory)
        additional_goals: Optional dict mapping goal names to winners
        host_candidates: Optional list of top host candidates
        award_candidates: Optional dict of per-award candidate lists
        additional_goals_candidates: Optional dict of additional goal candidate lists

    Returns:
        Tuple of (json_path, text_path)
    """
    results = build_json_output(
        hosts, awards, award_data, additional_goals, host_candidates, award_candidates, additional_goals_candidates
    )

    # Write both output files
    json_path = write_json_output(results, year, output_dir)
    text_path = write_text_output(results, year, output_dir)

    return json_path, text_path
