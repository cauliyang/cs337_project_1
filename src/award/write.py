"""Output generation for Golden Globes extraction results."""

import json
from pathlib import Path


def write_json_output(results: dict, year: str, output_dir: str = ".") -> Path:
    """
    Write extraction results to JSON file in autograder-compatible format.

    Args:
        results: Dictionary with keys 'hosts', 'awards', 'award_data'
        year: Year string (e.g., "2013")
        output_dir: Directory to write output file (default: current directory)

    Returns:
        Path to the created JSON file

    Raises:
        ValueError: If results dictionary is missing required keys
    """
    # Validate required keys
    required_keys = {"hosts", "awards", "award_data"}
    if not required_keys.issubset(results.keys()):
        missing = required_keys - results.keys()
        raise ValueError(f"Results missing required keys: {missing}")

    # Validate award_data structure (not awards list, which can be dynamically discovered)
    # Note: awards list can contain discovered awards, while award_data uses template awards
    for award, award_obj in results.get("award_data", {}).items():
        required_award_keys = {"presenters", "nominees", "winner"}
        if not required_award_keys.issubset(award_obj.keys()):
            missing = required_award_keys - award_obj.keys()
            raise ValueError(f"Award '{award}' missing required keys: {missing}")

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
        results: Dictionary with keys 'hosts', 'awards', 'award_data'
        year: Year string (e.g., "2013")
        output_dir: Directory to write output file (default: current directory)

    Returns:
        Path to the created text file

    Raises:
        ValueError: If results dictionary is missing required keys
    """
    # Validate required keys
    required_keys = {"hosts", "awards", "award_data"}
    if not required_keys.issubset(results.keys()):
        missing = required_keys - results.keys()
        raise ValueError(f"Results missing required keys: {missing}")

    # Build output content
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append(f"Golden Globes {year} - Extraction Results")
    lines.append("=" * 60)
    lines.append("")

    # Hosts
    lines.append("HOSTS")
    lines.append("-" * 60)
    if results["hosts"]:
        for host in results["hosts"]:
            # Convert to title case for readability
            lines.append(f"- {host.title()}")
    else:
        lines.append("- (No hosts extracted)")
    lines.append("")

    # Awards & Winners
    lines.append("AWARDS & WINNERS")
    lines.append("-" * 60)

    for award in results["awards"]:
        award_data = results["award_data"].get(award, {})

        # Award name (title case)
        lines.append("")
        lines.append(award.title())

        # Winner
        winner = award_data.get("winner", "")
        if winner:
            lines.append(f"  Winner: {winner.title()}")
        else:
            lines.append("  Winner: (Not extracted)")

        # Nominees
        nominees = award_data.get("nominees", [])
        if nominees:
            lines.append("  Nominees:")
            for nominee in nominees:
                lines.append(f"    - {nominee.title()}")
        elif "cecil" not in award.lower():
            # Only show message if not Cecil B. DeMille (which has no nominees)
            lines.append("  Nominees: (Not extracted)")

        # Presenters
        presenters = award_data.get("presenters", [])
        if presenters:
            lines.append("  Presenters:")
            for presenter in presenters:
                lines.append(f"    - {presenter.title()}")

    # Create output file path
    output_path = Path(output_dir) / f"gg{year}_results.txt"

    # Write text file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Human-readable results written to {output_path}")
    return output_path


def build_json_output(hosts: list[str], awards: list[str], award_data: dict) -> dict:
    """
    Build JSON output structure from extraction results.

    Args:
        hosts: List of normalized host names
        awards: List of normalized award names
        award_data: Dictionary mapping award names to data (presenters, nominees, winner)

    Returns:
        Dictionary with proper structure for JSON output
    """
    return {
        "hosts": hosts,
        "awards": awards,
        "award_data": award_data,
    }


def generate_outputs(
    hosts: list[str],
    awards: list[str],
    award_data: dict,
    year: str,
    output_dir: str = ".",
) -> tuple[Path, Path]:
    """
    Generate both JSON and human-readable output files.

    Args:
        hosts: List of normalized host names
        awards: List of normalized award names
        award_data: Dictionary mapping award names to data
        year: Year string (e.g., "2013")
        output_dir: Directory to write output files (default: current directory)

    Returns:
        Tuple of (json_path, text_path)
    """
    # Build output structure
    results = build_json_output(hosts, awards, award_data)

    # Write both output files
    json_path = write_json_output(results, year, output_dir)
    text_path = write_text_output(results, year, output_dir)

    return json_path, text_path
