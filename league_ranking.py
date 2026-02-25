"""
League Ranking Calculator
Reads soccer match results and outputs a ranked league table.

Usage:
    python3.14 league_ranking.py input.txt
    cat input.txt | python3.14 league_ranking.py
"""

import sys
import argparse
from collections import defaultdict


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
    """Parse all input lines, skipping blank ones."""
    results = []
    for line in lines:
        if line.strip():
            results.append(parse_result(line))
    return results


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
        "filename",
        nargs="?",
        help="Path to input file (reads from stdin if omitted)",
    )
    args = parser.parse_args()

    lines = get_input_lines(args.filename)
    results = parse_input(lines)
    points = calculate_points(results)
    ranked = rank_teams(points)
    print(format_table(ranked))


if __name__ == "__main__":
    main()
