
"""
League Ranking Calculator
Reads soccer match results and outputs a ranked league table.

Usage:
    # v1 — single file or stdin
    python3.14 league_ranking.py input.txt
    cat input.txt | python3.14 league_ranking.py

    # v2 — directory or dated stdin blocks
    python3.14 league_ranking.py -r  results/
    python3.14 league_ranking.py -rl results/
    python3.14 league_ranking.py -rv results/
    cat all_results.txt | python3.14 league_ranking.py -r
"""

import os
import re
import sys
import argparse
from collections import defaultdict
from datetime import date, datetime

# ---------------------------------------------------------------------------
# Input loading
# ---------------------------------------------------------------------------

DateBlock = tuple[date, list[str]]  # (date, raw result lines)


def load_directory(path: str) -> list[DateBlock]:
    """
    Load all .txt files from a directory, detect their date, and return
    a chronologically sorted list of (date, lines) pairs.
    Files that cannot be dated emit a warning and are skipped.
    """
    blocks: list[DateBlock] = []

    for filename in sorted(os.listdir(path)):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(path, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        d = parse_date_from_file(filepath, lines)
        if d is None:
            print(f"Warning: could not determine date for '{filename}', skipping.", file=sys.stderr)
            continue

        # Strip the date header line from content if it was inside the file
        content = [
            l for l in lines
            if not _is_date_header(l.strip()) and parse_date_from_string(l.strip()) != d
        ]
        blocks.append((d, content))

    return sorted(blocks, key=lambda b: b[0])


def load_stdin_blocks(lines: list[str]) -> list[DateBlock]:
    """
    Split stdin into dated blocks. A new block starts whenever a date
    header line is encountered (DATE: YYYY-MM-DD or # YYYY-MM-DD).
    Blocks are sorted chronologically before returning.
    Lines before the first date header are ignored with a warning.
    """
    blocks: list[DateBlock] = []
    current_date: date | None = None
    current_lines: list[str] = []
    orphan_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        d = parse_date_from_string(stripped) if _is_date_header(stripped) else None

        if d is not None:
            if current_date is not None:
                blocks.append((current_date, current_lines))
            elif orphan_lines:
                print("Warning: lines before first date header were ignored.", file=sys.stderr)
            current_date = d
            current_lines = []
        else:
            if current_date is None:
                orphan_lines.append(line)
            else:
                current_lines.append(line)

    if current_date is not None:
        blocks.append((current_date, current_lines))
    elif orphan_lines:
        print("Warning: no date headers found in stdin; no output produced.", file=sys.stderr)

    return sorted(blocks, key=lambda b: b[0])


def get_dated_blocks(source: str | None) -> list[DateBlock]:
    """
    Return dated blocks from a directory path or from stdin.
    """
    if source and os.path.isdir(source):
        return load_directory(source)
    lines = sys.stdin.readlines() if not source else []
    return load_stdin_blocks(lines)

# ---------------------------------------------------------------------------
# Parsing 
# ---------------------------------------------------------------------------

def parse_result(line: str) -> tuple[str, int, str, int]:
    """
    Parse a single result line into two (team, score) pairs.

    Expected format: 'Team A <score>, Team B <score>'
    Returns: (team1, score1, team2, score2)
    Raises: ValueError if the line cannot be parsed.
    """
    try:
        left, right = line.strip().split(",", 1)
        team1, score1 = left.strip().rsplit(" ", 1)
        team2, score2 = right.strip().rsplit(" ", 1)
        return team1.strip(), int(score1), team2.strip(), int(score2)
    except Exception:
        raise ValueError(f"Could not parse line: '{line.strip()}'")


def parse_input(lines: list[str]) -> list[tuple[str, int, str, int]]:
    """Parse all input lines, skipping blank ones and date headers."""
    results = []
    for line in lines:
        stripped = line.strip()
        if stripped and not _is_date_header(stripped):
            results.append(parse_result(line))
    return results

_DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")

_DATE_HEADER_PATTERN = re.compile(
    r"^\s*(?:DATE:\s*|#\s*)(\d{4}-\d{2}-\d{2})\s*$", re.IGNORECASE
)


def _is_date_header(line: str) -> bool:
    """Return True if the line is a date header (DATE: or # format)."""
    return bool(_DATE_HEADER_PATTERN.match(line))


def parse_date_from_string(text: str) -> date | None:
    """
    Extract an ISO date (YYYY-MM-DD) from a string.
    Accepts:
        - 'DATE: 2024-01-15'
        - '# 2024-01-15'
        - '2024-01-15'          (bare date, e.g. first line of a file)
        - '2024-01-15.txt'      (filename)
    Returns a date object or None if no date found.
    """
    match = _DATE_PATTERN.search(text)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_date_from_file(filepath: str, lines: list[str]) -> date | None:
    """
    Try to determine the date for a file by checking:
    1. The filename itself.
    2. The first non-blank line of the file.
    Returns a date object or None.
    """
    d = parse_date_from_string(os.path.basename(filepath))
    if d:
        return d
    for line in lines:
        if line.strip():
            return parse_date_from_string(line.strip())
    return None

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def calculate_points(results: list[tuple[str, int, str, int]]) -> dict[str, int]:
    """
    Calculate total points for each team from match results.

    Win  = 3 pts
    Draw = 1 pt
    Loss = 0 pts
    """
    points: dict[str, int] = defaultdict(int)

    for team1, score1, team2, score2 in results:
        # Ensure both teams appear in the table even with 0 points
        points[team1] += 0
        points[team2] += 0

        if score1 > score2:
            points[team1] += 3
        elif score2 > score1:
            points[team2] += 3
        else:
            points[team1] += 1
            points[team2] += 1

    return dict(points)


# ---------------------------------------------------------------------------
# Sorting & Ranking 
# ---------------------------------------------------------------------------

def rank_teams(points: dict[str, int]) -> list[tuple[int, str, int]]:
    """
    Sort teams by points (desc), then alphabetically on ties.
    Returns a list of (rank, team_name, points) tuples.
    """
    sorted_teams = sorted(points.items(), key=lambda x: (-x[1], x[0]))

    ranked = []
    rank = 1
    for i, (team, pts) in enumerate(sorted_teams):
        if i > 0 and pts < sorted_teams[i - 1][1]:
            rank = i + 1
        ranked.append((rank, team, pts))

    return ranked


# ---------------------------------------------------------------------------
# Formatting 
# ---------------------------------------------------------------------------

def format_points(pts: int) -> str:
    """Return '1 pt' for exactly 1 point, '<n> pts' otherwise."""
    return f"{pts} pt" if pts == 1 else f"{pts} pts"


def format_table(ranked: list[tuple[int, str, int]]) -> str:
    """Format the ranked list into the final output string."""
    lines = []
    for rank, team, pts in ranked:
        lines.append(f"{rank}. {team}, {format_points(pts)}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Recursive modes 
# ---------------------------------------------------------------------------

def run_recursive(blocks: list[DateBlock]) -> None:
    """
    -r / --recursive
    Combine all dated blocks into one global ranking and print it.
    """
    all_results = []
    for _, lines in blocks:
        all_results.extend(parse_input(lines))

    points = calculate_points(all_results)
    ranked = rank_teams(points)
    print(format_table(ranked))


def run_recursive_local(blocks: list[DateBlock]) -> None:
    """
    -rl / --recursive-local
    Print a separate ranking table for each date, in chronological order.
    """
    sections = []
    for d, lines in blocks:
        results = parse_input(lines)
        points = calculate_points(results)
        ranked = rank_teams(points)
        sections.append(f"=== {d} ===\n{format_table(ranked)}")

    print("\n\n".join(sections))


def run_recursive_verbose(blocks: list[DateBlock]) -> None:
    """
    -rv / --recursive-verbose
    Print the cumulative global ranking after each date so you can see
    how the table evolves over time.
    """
    cumulative_results = []
    sections = []

    for d, lines in blocks:
        cumulative_results.extend(parse_input(lines))
        points = calculate_points(cumulative_results)
        ranked = rank_teams(points)
        sections.append(f"=== After {d} ===\n{format_table(ranked)}")

    print("\n\n".join(sections))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def get_input_lines(filename: str | None) -> list[str]:
    """Read lines from a file or stdin."""
    if filename:
        with open(filename, "r", encoding="utf-8") as f:
            return f.readlines()
    return sys.stdin.readlines()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate the ranking table for a league."
    )
    parser.add_argument(
        "source",
        nargs="?",
        help=(
            "Path to input file or directory for recursive modes"
            "Reads from stdin if omitted."
        ),
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Combine all dated inputs and output one global ranking.",
    )
    mode.add_argument(
        "-rl", "--recursive-local",
        action="store_true",
        help="Output a separate ranking table per date, in chronological order.",
    )
    mode.add_argument(
        "-rv", "--recursive-verbose",
        action="store_true",
        help="Output the cumulative global ranking after each date.",
    )

    args = parser.parse_args()

    # recursive modes
    if args.recursive or args.recursive_local or args.recursive_verbose:
        blocks = get_dated_blocks(args.source)
        if not blocks:
            print("No dated input blocks found.", file=sys.stderr)
            sys.exit(1)

        if args.recursive:
            run_recursive(blocks)
        elif args.recursive_local:
            run_recursive_local(blocks)
        else:
            run_recursive_verbose(blocks)
        return

    # single mode
    lines = get_input_lines(args.source)
    results = parse_input(lines)
    points = calculate_points(results)
    ranked = rank_teams(points)
    print(format_table(ranked))


if __name__ == "__main__":
    main()
