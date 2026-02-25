
# League Ranking Calculator

A production-ready command-line application that reads soccer match results from a file or stdin and outputs a ranked league table.

---

## Requirements

- Python 3.14.3
- No external dependencies — standard library only

---

## Project Structure

```
league-ranking/
├── league_ranking.py       # Main application logic + CLI entry point
├── test_league_ranking.py  # Unit tests
└── README.md
```

---

## Usage

### Via file argument

```bash
python3.14 league_ranking.py input.txt
```

### Via stdin

```bash
cat input.txt | python3.14 league_ranking.py
```

---

## Input Format

One match result per line, in the following format:

```
Team A <score>, Team B <score>
```

Team names may contain spaces. Example input file:

```
Lions 3, Snakes 3
Tarantulas 1, FC Awesome 0
Lions 1, FC Awesome 1
Tarantulas 3, Snakes 1
Lions 4, Grouches 0
```

---

## Output Format

Teams are ranked from most to least points. Teams tied on points share the same rank and are listed alphabetically. The word "pt" is used for exactly 1 point, "pts" for everything else.

Expected output for the sample above:

```
1. Tarantulas, 6 pts
2. Lions, 5 pts
3. FC Awesome, 1 pt
3. Snakes, 1 pt
5. Grouches, 0 pts
```

---

## Scoring Rules

| Result | Points |
|--------|--------|
| Win    | 3      |
| Draw   | 1      |
| Loss   | 0      |

---

## Running the Tests

```bash
python3.14 -m unittest test_league_ranking.py
```

To run with verbose output:

```bash
python3.14 -m unittest test_league_ranking.py -v
```

---

## Edge Cases Handled

- Team names containing spaces (e.g. `FC Awesome`)
- Teams that finish with 0 points still appear in the table
- Multi-digit scores
- Two or more teams tied on points share the same rank; the next rank skips accordingly (e.g. two teams tied at 3rd means the next rank is 5th)
- Correct "pt" vs "pts" grammar
- Blank lines in input are ignored
