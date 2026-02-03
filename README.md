# Achievement Engine — Finish Next

Overview
--------
Small Python tool that analyzes TrueAchievements CSV exports and recommends which games to "finish next" based on progress, remaining effort (Gamerscore), risk (unachievable achievements), and TA value.

Important constraints
- Grouping is done only by `GameName` (no reliable game-level ID in exports).
- Input is two CSV files exported manually from TrueAchievements and placed under `data/`:
  - `data/unlocked.csv` — unlocked achievements export
  - `data/locked.csv` — locked achievements export

Quick start
-----------
1. Place your CSV exports in `data/unlocked.csv` and `data/locked.csv`.
2. Run the script (defaults):

```bash
python rank_next.py
```

Common options
--------------
- `--mode fast|ratio|safe` — apply preset weighting strategies (fast finishes, TA ratio-focused, or safe/low-risk).
- `--top N` / `-n N` — show top N recommendations (default from `config.json` or built-in `TOP_N`).
- `--include-dlc` / `--exclude-dlc` — include or ignore DLC achievements.
- `--count-unachievable` / `--no-count-unachievable` — include unachievable locked achievements in totals.
- `--verbose` / `-v` — print expanded profile stats (completion buckets + secondary reports).

- `--ta-buckets` — print counts and percentages of achievements grouped by TA ratio buckets (earned vs remaining achievable).
- `--ta-bucket-edges "e1,e2,..."` — optional comma-separated numeric upper bounds for TA buckets (example: `"1.4,1.81,2.3,3,4,6"`).

Examples
--------
Show top 10 prioritized by TA ratio:

```bash
python rank_next.py --mode ratio --top 10
```

Use fast preset and include DLC:

```bash
python rank_next.py --mode fast --include-dlc
```

Configuration (`config.json`)
----------------------------
You can place a `config.json` next to `rank_next.py` to set defaults and override weights. CLI flags override `config.json` values.

Example `config.json`:

```json
{
  "mode": "safe",
  "TOP_N": 20,
  "INCLUDE_DLC": true,
  "COUNT_UNACHIEVABLE_IN_TOTAL": false,
  "W_COMPLETION": 60,
  "W_RATIO_OPPORTUNITY": 20,
  "verbose": true
}
```

Precedence order
- CLI flags > `config.json` > built-in defaults in `rank_next.py`.

Output notes
------------
- Recommendations are Gamerscore-based completion suggestions (not raw achievement counts).
- Per-game `Why` lines explain weighted score contributions so you can see why a game ranked where it did.
- Secondary reports (when verbose) summarize blocked games, DLC-only remaining games, and total GS lost to unachievable achievements.

Testing
-------
Run unit tests:

```bash
python -m unittest tests.test_rank_next -v
```

TA buckets report
-----------------
To print the TA ratio bucket summary (earned vs remaining achievable), run:

```bash
python rank_next.py --ta-buckets
```

With custom bucket edges:

```bash
python rank_next.py --ta-buckets --ta-bucket-edges "1.4,1.81,2.3,3,4,6"
```

TA bucketed achievement lists
-----------------------------
To print the achievements grouped by TA ratio buckets, use `--ta-list`.

List both earned and remaining achievable (default):

```bash
python rank_next.py --ta-list
```

List only earned achievements:

```bash
python rank_next.py --ta-list --ta-list-type earned
```

List only remaining achievable locked achievements:

```bash
python rank_next.py --ta-list --ta-list-type remaining
```

You can combine with `--ta-bucket-edges` to customize bucket ranges.

Per-bucket command
------------------
To print a single bucket (both unlocked and locked achievements, separated), use either the 1-based index or the exact label:

By index (1-based):

```bash
python rank_next.py --ta-bucket-index 1
```

By label (must match one of the printed labels, e.g. '0.00-1.40' or '>6.00'):

```bash
python rank_next.py --ta-bucket-label ">6.00"
```

Both accept `--ta-bucket-edges` to change the bucket ranges.

Where to next
-------------
- Tweak presets or individual weights in `config.json`.
- Add CLI flags to change individual weights at runtime (available on request).

File references
---------------
- Script: `rank_next.py`
- Tests: `tests/test_rank_next.py`
- Config: `config.json` (optional)
- Data directory: `data/` (place `unlocked.csv` and `locked.csv` here)

Enjoy — if you'd like, I can add README examples showing `config.json` presets side-by-side or add CLI flags to set individual weights.
