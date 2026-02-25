
"""
Unit tests for League Ranking Calculator.

Run with:
    python3.14 -m unittest test_league_ranking.py -v
"""

import os
import sys
import tempfile
import unittest
from datetime import date
from unittest.mock import patch

from league_ranking import (
    # v1
    parse_result,
    parse_input,
    calculate_points,
    rank_teams,
    format_points,
    format_table,
    # v2
    parse_date_from_string,
    parse_date_from_file,
    load_directory,
    load_stdin_blocks,
    run_recursive,
    run_recursive_local,
    run_recursive_verbose,
)


# ---------------------------------------------------------------------------
# parse_result
# ---------------------------------------------------------------------------

class TestParseResult(unittest.TestCase):

    def test_simple_team_names(self):
        self.assertEqual(parse_result("Lions 3, Snakes 3"), ("Lions", 3, "Snakes", 3))

    def test_team_name_with_spaces(self):
        self.assertEqual(parse_result("FC Awesome 1, Lions 1"), ("FC Awesome", 1, "Lions", 1))

    def test_zero_scores(self):
        self.assertEqual(parse_result("Grouches 0, Lions 4"), ("Grouches", 0, "Lions", 4))

    def test_multi_digit_scores(self):
        self.assertEqual(parse_result("Lions 10, Snakes 12"), ("Lions", 10, "Snakes", 12))

    def test_whitespace_is_stripped(self):
        self.assertEqual(parse_result("  Lions 3,  Snakes 3  "), ("Lions", 3, "Snakes", 3))

    def test_invalid_line_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_result("not a valid line")

    def test_missing_score_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_result("Lions, Snakes 3")


# ---------------------------------------------------------------------------
# parse_input
# ---------------------------------------------------------------------------

class TestParseInput(unittest.TestCase):

    def test_parses_multiple_lines(self):
        lines = [
            "Lions 3, Snakes 3\n",
            "Tarantulas 1, FC Awesome 0\n",
        ]
        result = parse_input(lines)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ("Lions", 3, "Snakes", 3))
        self.assertEqual(result[1], ("Tarantulas", 1, "FC Awesome", 0))

    def test_skips_blank_lines(self):
        lines = ["Lions 3, Snakes 3\n", "\n", "  \n", "Tarantulas 1, FC Awesome 0\n"]
        result = parse_input(lines)
        self.assertEqual(len(result), 2)

    def test_skips_date_header_style_date(self):
        lines = ["DATE: 2024-01-15\n", "Lions 3, Snakes 3\n"]
        result = parse_input(lines)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], ("Lions", 3, "Snakes", 3))

    def test_skips_hash_style_date_header(self):
        lines = ["# 2024-01-15\n", "Lions 3, Snakes 3\n"]
        result = parse_input(lines)
        self.assertEqual(len(result), 1)

    def test_empty_input_returns_empty_list(self):
        self.assertEqual(parse_input([]), [])


# ---------------------------------------------------------------------------
# calculate_points
# ---------------------------------------------------------------------------

class TestCalculatePoints(unittest.TestCase):

    def test_win_gives_three_points(self):
        results = [("Lions", 3, "Snakes", 1)]
        points = calculate_points(results)
        self.assertEqual(points["Lions"], 3)
        self.assertEqual(points["Snakes"], 0)

    def test_loss_gives_zero_points(self):
        results = [("Lions", 0, "Snakes", 2)]
        points = calculate_points(results)
        self.assertEqual(points["Lions"], 0)
        self.assertEqual(points["Snakes"], 3)

    def test_draw_gives_one_point_each(self):
        results = [("Lions", 1, "Snakes", 1)]
        points = calculate_points(results)
        self.assertEqual(points["Lions"], 1)
        self.assertEqual(points["Snakes"], 1)

    def test_points_accumulate_across_matches(self):
        results = [
            ("Lions", 3, "Snakes", 3),
            ("Lions", 1, "FC Awesome", 1),
            ("Lions", 4, "Grouches", 0),
        ]
        points = calculate_points(results)
        self.assertEqual(points["Lions"], 5)
        self.assertEqual(points["Snakes"], 1)
        self.assertEqual(points["FC Awesome"], 1)
        self.assertEqual(points["Grouches"], 0)

    def test_all_teams_appear_even_with_zero_points(self):
        results = [("Lions", 5, "Grouches", 0)]
        points = calculate_points(results)
        self.assertIn("Grouches", points)
        self.assertEqual(points["Grouches"], 0)

    def test_sample_input(self):
        results = [
            ("Lions", 3, "Snakes", 3),
            ("Tarantulas", 1, "FC Awesome", 0),
            ("Lions", 1, "FC Awesome", 1),
            ("Tarantulas", 3, "Snakes", 1),
            ("Lions", 4, "Grouches", 0),
        ]
        points = calculate_points(results)
        self.assertEqual(points["Tarantulas"], 6)
        self.assertEqual(points["Lions"], 5)
        self.assertEqual(points["FC Awesome"], 1)
        self.assertEqual(points["Snakes"], 1)
        self.assertEqual(points["Grouches"], 0)


# ---------------------------------------------------------------------------
# rank_teams
# ---------------------------------------------------------------------------

class TestRankTeams(unittest.TestCase):

    def test_ranked_by_points_descending(self):
        points = {"Lions": 5, "Tarantulas": 6, "Grouches": 0}
        ranked = rank_teams(points)
        self.assertEqual(ranked[0], (1, "Tarantulas", 6))
        self.assertEqual(ranked[1], (2, "Lions", 5))
        self.assertEqual(ranked[2], (3, "Grouches", 0))

    def test_tied_teams_share_rank(self):
        points = {"FC Awesome": 1, "Snakes": 1}
        ranked = rank_teams(points)
        self.assertEqual(ranked[0][0], ranked[1][0])

    def test_tied_teams_are_alphabetical(self):
        points = {"Snakes": 1, "FC Awesome": 1}
        ranked = rank_teams(points)
        self.assertEqual(ranked[0][1], "FC Awesome")
        self.assertEqual(ranked[1][1], "Snakes")

    def test_rank_skips_after_tie(self):
        points = {"FC Awesome": 1, "Snakes": 1, "Tarantulas": 6, "Lions": 5, "Grouches": 0}
        ranked = rank_teams(points)
        ranks = {team: rank for rank, team, _ in ranked}
        self.assertEqual(ranks["Tarantulas"], 1)
        self.assertEqual(ranks["Lions"], 2)
        self.assertEqual(ranks["FC Awesome"], 3)
        self.assertEqual(ranks["Snakes"], 3)
        self.assertEqual(ranks["Grouches"], 5)  # skips 4

    def test_three_way_tie(self):
        points = {"Alpha": 3, "Beta": 3, "Gamma": 3}
        ranked = rank_teams(points)
        self.assertTrue(all(rank == 1 for rank, _, _ in ranked))

    def test_single_team(self):
        ranked = rank_teams({"Lions": 9})
        self.assertEqual(ranked, [(1, "Lions", 9)])

    def test_empty_input(self):
        self.assertEqual(rank_teams({}), [])


# ---------------------------------------------------------------------------
# format_points
# ---------------------------------------------------------------------------

class TestFormatPoints(unittest.TestCase):

    def test_zero_points(self):
        self.assertEqual(format_points(0), "0 pts")

    def test_one_point(self):
        self.assertEqual(format_points(1), "1 pt")

    def test_two_points(self):
        self.assertEqual(format_points(2), "2 pts")

    def test_large_number(self):
        self.assertEqual(format_points(100), "100 pts")


# ---------------------------------------------------------------------------
# format_table
# ---------------------------------------------------------------------------

class TestFormatTable(unittest.TestCase):

    def test_sample_output(self):
        ranked = [
            (1, "Tarantulas", 6),
            (2, "Lions", 5),
            (3, "FC Awesome", 1),
            (3, "Snakes", 1),
            (5, "Grouches", 0),
        ]
        expected = (
            "1. Tarantulas, 6 pts\n"
            "2. Lions, 5 pts\n"
            "3. FC Awesome, 1 pt\n"
            "3. Snakes, 1 pt\n"
            "5. Grouches, 0 pts"
        )
        self.assertEqual(format_table(ranked), expected)

    def test_single_team(self):
        ranked = [(1, "Lions", 9)]
        self.assertEqual(format_table(ranked), "1. Lions, 9 pts")

    def test_empty_table(self):
        self.assertEqual(format_table([]), "")


# ---------------------------------------------------------------------------
# parse_date_from_string
# ---------------------------------------------------------------------------

class TestParseDateFromString(unittest.TestCase):

    def test_bare_date(self):
        self.assertEqual(parse_date_from_string("2024-01-15"), date(2024, 1, 15))

    def test_date_header_style(self):
        self.assertEqual(parse_date_from_string("DATE: 2024-01-15"), date(2024, 1, 15))

    def test_hash_style_header(self):
        self.assertEqual(parse_date_from_string("# 2024-01-15"), date(2024, 1, 15))

    def test_date_in_filename(self):
        self.assertEqual(parse_date_from_string("2024-01-15.txt"), date(2024, 1, 15))

    def test_no_date_returns_none(self):
        self.assertIsNone(parse_date_from_string("Lions 3, Snakes 3"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(parse_date_from_string(""))

    def test_invalid_date_returns_none(self):
        self.assertIsNone(parse_date_from_string("2024-99-99"))


# ---------------------------------------------------------------------------
# parse_date_from_file
# ---------------------------------------------------------------------------

class TestParseDateFromFile(unittest.TestCase):

    def test_date_from_filename(self):
        d = parse_date_from_file("/results/2024-01-15.txt", [])
        self.assertEqual(d, date(2024, 1, 15))

    def test_date_from_first_line_bare(self):
        d = parse_date_from_file("/results/matchday.txt", ["2024-03-10\n", "Lions 3, Snakes 1\n"])
        self.assertEqual(d, date(2024, 3, 10))

    def test_date_from_first_line_date_header(self):
        d = parse_date_from_file("/results/matchday.txt", ["DATE: 2024-03-10\n", "Lions 3, Snakes 1\n"])
        self.assertEqual(d, date(2024, 3, 10))

    def test_filename_takes_priority_over_first_line(self):
        d = parse_date_from_file("/results/2024-01-15.txt", ["2024-06-20\n", "Lions 3, Snakes 1\n"])
        self.assertEqual(d, date(2024, 1, 15))

    def test_no_date_returns_none(self):
        d = parse_date_from_file("/results/matchday.txt", ["Lions 3, Snakes 1\n"])
        self.assertIsNone(d)

    def test_skips_blank_lines_for_first_line_check(self):
        d = parse_date_from_file("/results/matchday.txt", ["\n", "  \n", "2024-05-01\n"])
        self.assertEqual(d, date(2024, 5, 1))


# ---------------------------------------------------------------------------
# load_directory
# ---------------------------------------------------------------------------

class TestLoadDirectory(unittest.TestCase):

    def _make_dir(self, files: dict[str, str]) -> str:
        """Create a temp directory with the given filename->content mapping."""
        tmpdir = tempfile.mkdtemp()
        for name, content in files.items():
            with open(os.path.join(tmpdir, name), "w") as f:
                f.write(content)
        return tmpdir

    def test_loads_files_by_filename_date(self):
        tmpdir = self._make_dir({
            "2024-01-15.txt": "Lions 3, Snakes 1\n",
            "2024-01-16.txt": "Tarantulas 1, FC Awesome 0\n",
        })
        blocks = load_directory(tmpdir)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0][0], date(2024, 1, 15))
        self.assertEqual(blocks[1][0], date(2024, 1, 16))

    def test_loads_files_by_first_line_date(self):
        tmpdir = self._make_dir({
            "matchday1.txt": "2024-02-01\nLions 3, Snakes 1\n",
        })
        blocks = load_directory(tmpdir)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0][0], date(2024, 2, 1))

    def test_sorts_blocks_chronologically(self):
        tmpdir = self._make_dir({
            "2024-03-10.txt": "Lions 3, Snakes 1\n",
            "2024-01-05.txt": "Tarantulas 1, FC Awesome 0\n",
            "2024-06-20.txt": "Grouches 0, Lions 4\n",
        })
        blocks = load_directory(tmpdir)
        dates = [b[0] for b in blocks]
        self.assertEqual(dates, sorted(dates))

    def test_skips_undatable_files_with_warning(self):
        tmpdir = self._make_dir({
            "2024-01-15.txt": "Lions 3, Snakes 1\n",
            "nodatehere.txt": "Tarantulas 1, FC Awesome 0\n",
        })
        with patch("sys.stderr"):
            blocks = load_directory(tmpdir)
        self.assertEqual(len(blocks), 1)

    def test_ignores_non_txt_files(self):
        tmpdir = self._make_dir({
            "2024-01-15.txt": "Lions 3, Snakes 1\n",
            "2024-01-16.csv": "ignored content\n",
        })
        blocks = load_directory(tmpdir)
        self.assertEqual(len(blocks), 1)

    def test_date_header_stripped_from_content(self):
        tmpdir = self._make_dir({
            "matchday.txt": "DATE: 2024-04-01\nLions 3, Snakes 1\n",
        })
        blocks = load_directory(tmpdir)
        results = parse_input(blocks[0][1])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], ("Lions", 3, "Snakes", 1))

    def test_empty_directory_returns_empty_list(self):
        tmpdir = tempfile.mkdtemp()
        blocks = load_directory(tmpdir)
        self.assertEqual(blocks, [])


# ---------------------------------------------------------------------------
# load_stdin_blocks
# ---------------------------------------------------------------------------

class TestLoadStdinBlocks(unittest.TestCase):

    def test_date_header_style(self):
        lines = [
            "DATE: 2024-01-15\n",
            "Lions 3, Snakes 3\n",
            "DATE: 2024-01-16\n",
            "Tarantulas 3, Snakes 1\n",
        ]
        blocks = load_stdin_blocks(lines)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0][0], date(2024, 1, 15))
        self.assertEqual(blocks[1][0], date(2024, 1, 16))

    def test_hash_header_style(self):
        lines = [
            "# 2024-01-15\n",
            "Lions 3, Snakes 3\n",
            "# 2024-01-16\n",
            "Tarantulas 3, Snakes 1\n",
        ]
        blocks = load_stdin_blocks(lines)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0][0], date(2024, 1, 15))

    def test_mixed_header_styles(self):
        lines = [
            "DATE: 2024-01-15\n",
            "Lions 3, Snakes 3\n",
            "# 2024-01-16\n",
            "Tarantulas 3, Snakes 1\n",
        ]
        blocks = load_stdin_blocks(lines)
        self.assertEqual(len(blocks), 2)

    def test_sorts_out_of_order_dates(self):
        lines = [
            "DATE: 2024-03-01\n",
            "Lions 3, Snakes 1\n",
            "DATE: 2024-01-01\n",
            "Tarantulas 1, FC Awesome 0\n",
        ]
        blocks = load_stdin_blocks(lines)
        self.assertEqual(blocks[0][0], date(2024, 1, 1))
        self.assertEqual(blocks[1][0], date(2024, 3, 1))

    def test_orphan_lines_before_first_header_ignored(self):
        lines = [
            "Lions 3, Snakes 3\n",      # orphan — no date header yet
            "DATE: 2024-01-15\n",
            "Tarantulas 1, FC Awesome 0\n",
        ]
        with patch("sys.stderr"):
            blocks = load_stdin_blocks(lines)
        self.assertEqual(len(blocks), 1)
        results = parse_input(blocks[0][1])
        self.assertEqual(results[0], ("Tarantulas", 1, "FC Awesome", 0))

    def test_no_headers_returns_empty(self):
        lines = ["Lions 3, Snakes 3\n"]
        with patch("sys.stderr"):
            blocks = load_stdin_blocks(lines)
        self.assertEqual(blocks, [])

    def test_empty_input_returns_empty(self):
        self.assertEqual(load_stdin_blocks([]), [])

    def test_blank_lines_between_blocks_ignored(self):
        lines = [
            "DATE: 2024-01-15\n",
            "Lions 3, Snakes 3\n",
            "\n",
            "DATE: 2024-01-16\n",
            "Tarantulas 3, Snakes 1\n",
        ]
        blocks = load_stdin_blocks(lines)
        self.assertEqual(len(blocks), 2)


# ---------------------------------------------------------------------------
# run_recursive
# ---------------------------------------------------------------------------

class TestRunRecursive(unittest.TestCase):

    def _blocks(self):
        return [
            (date(2024, 1, 15), ["Lions 3, Snakes 3\n", "Tarantulas 1, FC Awesome 0\n"]),
            (date(2024, 1, 16), ["Tarantulas 3, Snakes 1\n", "Lions 4, Grouches 0\n"]),
            (date(2024, 1, 17), ["Lions 1, FC Awesome 1\n"]),
        ]

    def test_outputs_single_global_table(self, ):
        with patch("builtins.print") as mock_print:
            run_recursive(self._blocks())
        output = mock_print.call_args[0][0]
        self.assertIn("1. Tarantulas, 6 pts", output)
        self.assertIn("2. Lions, 5 pts", output)
        self.assertEqual(output.count("==="), 0)  # no section headers

    def test_combines_all_results(self):
        with patch("builtins.print") as mock_print:
            run_recursive(self._blocks())
        output = mock_print.call_args[0][0]
        # Grouches only appears in day 2 — must still be in global table
        self.assertIn("Grouches", output)

    def test_single_block(self):
        blocks = [(date(2024, 1, 15), ["Lions 3, Snakes 1\n"])]
        with patch("builtins.print") as mock_print:
            run_recursive(blocks)
        output = mock_print.call_args[0][0]
        self.assertIn("Lions", output)
        self.assertIn("Snakes", output)


# ---------------------------------------------------------------------------
# run_recursive_local
# ---------------------------------------------------------------------------

class TestRunRecursiveLocal(unittest.TestCase):

    def _blocks(self):
        return [
            (date(2024, 1, 15), ["Lions 3, Snakes 3\n"]),
            (date(2024, 1, 16), ["Tarantulas 3, Snakes 1\n"]),
        ]

    def test_outputs_section_per_date(self):
        with patch("builtins.print") as mock_print:
            run_recursive_local(self._blocks())
        output = mock_print.call_args[0][0]
        self.assertIn("=== 2024-01-15 ===", output)
        self.assertIn("=== 2024-01-16 ===", output)

    def test_each_section_is_independent(self):
        blocks = [
            (date(2024, 1, 15), ["Lions 3, Snakes 3\n"]),   # draw only
            (date(2024, 1, 16), ["Tarantulas 3, Snakes 1\n"]),  # Tarantulas wins
        ]
        with patch("builtins.print") as mock_print:
            run_recursive_local(blocks)
        output = mock_print.call_args[0][0]
        sections = output.split("\n\n")
        # Day 1: Lions and Snakes both 1pt — Tarantulas should NOT appear
        self.assertNotIn("Tarantulas", sections[0])
        # Day 2: Tarantulas 3pts — Lions should NOT appear
        self.assertNotIn("Lions", sections[1])

    def test_single_block(self):
        blocks = [(date(2024, 1, 15), ["Lions 3, Snakes 1\n"])]
        with patch("builtins.print") as mock_print:
            run_recursive_local(blocks)
        output = mock_print.call_args[0][0]
        self.assertIn("=== 2024-01-15 ===", output)


# ---------------------------------------------------------------------------
# run_recursive_verbose
# ---------------------------------------------------------------------------

class TestRunRecursiveVerbose(unittest.TestCase):

    def _blocks(self):
        return [
            (date(2024, 1, 15), ["Lions 3, Snakes 3\n", "Tarantulas 1, FC Awesome 0\n"]),
            (date(2024, 1, 16), ["Tarantulas 3, Snakes 1\n", "Lions 4, Grouches 0\n"]),
            (date(2024, 1, 17), ["Lions 1, FC Awesome 1\n"]),
        ]

    def test_outputs_section_per_date(self):
        with patch("builtins.print") as mock_print:
            run_recursive_verbose(self._blocks())
        output = mock_print.call_args[0][0]
        self.assertIn("=== After 2024-01-15 ===", output)
        self.assertIn("=== After 2024-01-16 ===", output)
        self.assertIn("=== After 2024-01-17 ===", output)

    def test_ranking_grows_cumulatively(self):
        blocks = [
            (date(2024, 1, 15), ["Lions 3, Snakes 1\n"]),
            (date(2024, 1, 16), ["Tarantulas 3, FC Awesome 0\n"]),
        ]
        with patch("builtins.print") as mock_print:
            run_recursive_verbose(blocks)
        output = mock_print.call_args[0][0]
        sections = output.split("\n\n")
        # Day 1: only Lions and Snakes
        self.assertNotIn("Tarantulas", sections[0])
        # Day 2 cumulative: all four teams present
        self.assertIn("Tarantulas", sections[1])
        self.assertIn("Lions", sections[1])

    def test_final_section_matches_global_ranking(self):
        blocks = self._blocks()
        # Get verbose output
        with patch("builtins.print") as mock_print:
            run_recursive_verbose(blocks)
        verbose_output = mock_print.call_args[0][0]
        final_section = verbose_output.split("\n\n")[-1]

        # Get global output
        with patch("builtins.print") as mock_print:
            run_recursive(blocks)
        global_output = mock_print.call_args[0][0]

        # Final verbose section (without header) should match global table
        final_table = "\n".join(final_section.split("\n")[1:])
        self.assertEqual(final_table, global_output)


# ---------------------------------------------------------------------------
# v1 Integration
# ---------------------------------------------------------------------------

class TestIntegration(unittest.TestCase):

    def test_full_sample(self):
        lines = [
            "Lions 3, Snakes 3\n",
            "Tarantulas 1, FC Awesome 0\n",
            "Lions 1, FC Awesome 1\n",
            "Tarantulas 3, Snakes 1\n",
            "Lions 4, Grouches 0\n",
        ]
        expected = (
            "1. Tarantulas, 6 pts\n"
            "2. Lions, 5 pts\n"
            "3. FC Awesome, 1 pt\n"
            "3. Snakes, 1 pt\n"
            "5. Grouches, 0 pts"
        )
        results = parse_input(lines)
        points = calculate_points(results)
        ranked = rank_teams(points)
        self.assertEqual(format_table(ranked), expected)

    def test_all_draws(self):
        lines = ["Alpha 1, Beta 1\n", "Alpha 1, Gamma 1\n", "Beta 1, Gamma 1\n"]
        results = parse_input(lines)
        points = calculate_points(results)
        ranked = rank_teams(points)
        self.assertTrue(all(rank == 1 for rank, _, _ in ranked))

    def test_all_same_winner(self):
        lines = ["Lions 3, Snakes 0\n", "Lions 3, FC Awesome 0\n"]
        results = parse_input(lines)
        points = calculate_points(results)
        ranked = rank_teams(points)
        self.assertEqual(ranked[0], (1, "Lions", 6))


# ---------------------------------------------------------------------------
# v2 End-to-end Integration
# ---------------------------------------------------------------------------

class TestV2Integration(unittest.TestCase):

    SAMPLE_BLOCKS = [
        (date(2024, 1, 15), [
            "Lions 3, Snakes 3\n",
            "Tarantulas 1, FC Awesome 0\n",
        ]),
        (date(2024, 1, 16), [
            "Lions 1, FC Awesome 1\n",
            "Tarantulas 3, Snakes 1\n",
        ]),
        (date(2024, 1, 17), [
            "Lions 4, Grouches 0\n",
        ]),
    ]

    def test_recursive_matches_manual_global(self):
        with patch("builtins.print") as mock_print:
            run_recursive(self.SAMPLE_BLOCKS)
        output = mock_print.call_args[0][0]
        self.assertEqual(
            output,
            "1. Tarantulas, 6 pts\n"
            "2. Lions, 5 pts\n"
            "3. FC Awesome, 1 pt\n"
            "3. Snakes, 1 pt\n"
            "5. Grouches, 0 pts",
        )

    def test_recursive_local_has_correct_number_of_sections(self):
        with patch("builtins.print") as mock_print:
            run_recursive_local(self.SAMPLE_BLOCKS)
        output = mock_print.call_args[0][0]
        # Each section header is "=== DATE ===" — two === per section
        self.assertEqual(output.count("==="), len(self.SAMPLE_BLOCKS) * 2)

    def test_recursive_verbose_section_count_matches_block_count(self):
        with patch("builtins.print") as mock_print:
            run_recursive_verbose(self.SAMPLE_BLOCKS)
        output = mock_print.call_args[0][0]
        self.assertEqual(output.count("=== After"), len(self.SAMPLE_BLOCKS))

    def test_directory_to_recursive_global(self):
        tmpdir = tempfile.mkdtemp()
        files = {
            "2024-01-15.txt": "Lions 3, Snakes 3\nTabrantulas 1, FC Awesome 0\n",
            "2024-01-16.txt": "Tarantulas 3, Snakes 1\nLions 4, Grouches 0\n",
        }
        for name, content in files.items():
            with open(os.path.join(tmpdir, name), "w") as f:
                f.write(content)

        from league_ranking import load_directory
        blocks = load_directory(tmpdir)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0][0], date(2024, 1, 15))
        self.assertEqual(blocks[1][0], date(2024, 1, 16))


if __name__ == "__main__":
    unittest.main()
