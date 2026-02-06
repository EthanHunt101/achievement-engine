# Achievement Engine

A Python tool that analyzes TrueAchievements CSV exports and provides visual dashboards showing your achievement progress, recommendations for games to finish next, and detailed DLC completion tracking.

## Features

- **Main Dashboard** (`page.html`) - Comprehensive overview with:
  - Profile summary (games started, completed, Gamerscore, TA Score)
  - Overall TA ratios (earned and possible)
  - Completion distribution charts
  - Top game recommendations
  - Blocked games (unachievable achievements)
  - Games with only DLC remaining
  - Complete list of all games with stats

- **DLC Checklist** (`dlc.html`) - Detailed DLC tracking:
  - Checklist of all DLCs organized by game
  - Completion status for each DLC
  - TA scores and ratios per DLC
  - Search and filter functionality

## Setup

Please refer to the SETUP.md file to go over the necessary steps to ensure the program runs correctly and with the correct csv files

## Settings

The program uses these defaults:
- **INCLUDE_DLC**: DLC achievements are included
- **COUNT_UNACHIEVABLE_IN_TOTAL**: Unachievable achievements are counted in totals

**Note:** Recommendations are ranked by number of remaining achievements (ascending) - games with fewer remaining achievements appear first. All recommendations are shown in the HTML dashboard.

To change these settings, edit the constants at the top of `rank_next.py`.

## File Structure

```
achievement-engine/
├── rank_next.py          # Main script
├── page.html             # Main dashboard
├── dlc.html              # DLC checklist page
├── data/                 # Your CSV files go here
│   ├── unlocked.csv      # Your unlocked achievements
│   └── locked.csv        # Your locked achievements
├── main_stats.json       # Generated (auto-created)
├── dlc_data.json         # Generated (auto-created)
└── README.md             # This file
```

## Output

The program generates two JSON files automatically:
- `main_stats.json` - All dashboard stats (profile summary, recommendations, blocked games, etc.)
- `dlc_data.json` - All DLC data for the checklist page

These are automatically created on every run and used by the HTML pages.

## Privacy

Your personal achievement data (CSV files and generated JSON) are excluded from version control via `.gitignore`. Only the code and HTML templates are shared.

## Troubleshooting

**"Missing data/unlocked.csv" error:**
- Make sure you've exported your CSV files from TrueAchievements
- Place them in the `data/` folder with exact names: `unlocked.csv` and `locked.csv`

**Numbers seem incorrect:**
- Verify your CSV exports are complete (TrueAchievements may have export limits)
- Check that all required columns are present in your CSV files

**HTML pages show "Loading..." or errors:**
- Make sure you've run `python rank_next.py` first to generate the JSON files
- Check that `main_stats.json` and `dlc_data.json` exist in the project root

## License

Free to use and modify as needed.
