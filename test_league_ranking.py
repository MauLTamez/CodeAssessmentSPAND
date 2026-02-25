"""
Unit tests for League Ranking Calculator.

Run with:
    python3.14 -m unittest test_league_ranking.py
"""

import unittest
from league_ranking import (
    parse_result,
    parse_input,
    calculate_points,
    rank_teams,
    format_points,
    format_table,
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
            ("Lions", 3, "Snakes", 3),   # draw: Lions 1, Snakes 1
            ("Lions", 1, "FC Awesome", 1), # draw: Lions 1, FC Awesome 1
            ("Lions", 4, "Grouches", 0),  # win: Lions 3
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
        self.assertEqual(ranked[0][0], ranked[1][0])  # same rank

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
# Integration test
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


if __name__ == "__main__":
    unittest.main()
