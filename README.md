# League Ranking Calculator

A production-ready command-line application that reads soccer match results from a file or stdin and outputs a ranked league table. Supports single-file mode as well as multi-date recursive modes for tracking league standings over time.

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

## Scoring Rules

| Result | Points |
|--------|--------|
| Win    | 3      |
| Draw   | 1      |
| Loss   | 0      |

---

## Usage

### Single file or stdin (default mode)

Reads one file or a stdin stream and outputs a single global ranking table.

```bash
# Via file argument
python3.14 league_ranking.py input.txt

# Via stdin
cat input.txt | python3.14 league_ranking.py
```

### `-r` / `--recursive` — Global ranking across multiple dates

Combines all dated inputs and outputs a single cumulative ranking table.

```bash
# From a directory of dated files
python3.14 league_ranking.py -r results/

# From a dated stdin stream
cat all_results.txt | python3.14 league_ranking.py -r
```

### `-rl` / `--recursive-local` — Per-date rankings

Outputs a separate ranking table for each date, in chronological order. Each section only reflects the results of that day.

```bash
python3.14 league_ranking.py -rl results/
cat all_results.txt | python3.14 league_ranking.py -rl
```

### `-rv` / `--recursive-verbose` — Cumulative ranking evolution

Outputs the cumulative global ranking after each date so you can see how the table evolved over time.

```bash
python3.14 league_ranking.py -rv results/
cat all_results.txt | python3.14 league_ranking.py -rv
```

---

## Input Formats

### Single file (default mode)

One match result per line:

```
Lions 3, Snakes 3
Tarantulas 1, FC Awesome 0
Lions 1, FC Awesome 1
Tarantulas 3, Snakes 1
Lions 4, Grouches 0
```

Team names may contain spaces (e.g. `FC Awesome`).

### Directory of dated files (recursive modes)

Each `.txt` file in the directory represents one matchday. The date is detected from either the filename or the first line of the file — whichever is found first.

**Date in filename:**
```
results/
├── 2024-01-15.txt
├── 2024-01-16.txt
└── 2024-01-17.txt
```

**Date as first line (bare or with header prefix):**
```
# contents of matchday1.txt
2024-01-15
Lions 3, Snakes 3
Tarantulas 1, FC Awesome 0
```

Files that cannot be dated are skipped with a warning printed to stderr.

### Stdin with date blocks (recursive modes)

Date headers split the stream into blocks. Both formats are accepted and can be mixed:

```
DATE: 2024-01-15
Lions 3, Snakes 3
Tarantulas 1, FC Awesome 0

# 2024-01-16
Tarantulas 3, Snakes 1
Lions 4, Grouches 0
```

Blocks are processed in chronological order regardless of the order they appear in the stream.

---

## Output Format

Teams are ranked from most to least points. Teams tied on points share the same rank and are listed alphabetically. The next rank after a tie skips accordingly.

`1 pt` is used for exactly one point; `pts` is used for everything else (including 0).

**Single / global output:**
```
1. Tarantulas, 6 pts
2. Lions, 5 pts
3. FC Awesome, 1 pt
3. Snakes, 1 pt
5. Grouches, 0 pts
```

**`-rl` per-date output:**
```
=== 2024-01-15 ===
1. Lions, 1 pt
1. Snakes, 1 pt
1. Tarantulas, 3 pts
...

=== 2024-01-16 ===
1. Tarantulas, 3 pts
2. Lions, 3 pts
...
```

**`-rv` verbose cumulative output:**
```
=== After 2024-01-15 ===
1. Tarantulas, 3 pts
2. Lions, 1 pt
...

=== After 2024-01-16 ===
1. Tarantulas, 6 pts
2. Lions, 4 pts
...
```

---

## Running the Tests

```bash
python3.14 -m unittest test_league_ranking.py
```

With verbose output:

```bash
python3.14 -m unittest test_league_ranking.py -v
```

---

## Edge Cases Handled

- Team names containing spaces (e.g. `FC Awesome`)
- Teams that finish with 0 points still appear in the table
- Multi-digit scores
- Two or more teams tied on points share the same rank; the next rank skips accordingly (e.g. two teams tied at 3rd means the next rank is 5th)
- Correct `pt` vs `pts` grammar
- Blank lines in input are ignored
- Date detected from filename or first line of file, with filename taking priority
- Both `DATE: YYYY-MM-DD` and `# YYYY-MM-DD` header formats accepted and can be mixed
- Stdin blocks processed in chronological order regardless of stream order
- Lines appearing before the first date header in a stdin stream are ignored with a warning
- Files with no detectable date are skipped with a warning
