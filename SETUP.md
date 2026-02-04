# Setup Guide

## Step-by-Step Instructions

### 1. Export Your Data from TrueAchievements

1. Log into [TrueAchievements](https://www.trueachievements.com/)
2. Navigate to your profile
3. Click the Achievements tab
4. Click the "More filter options" tab under Export
5. IMPORTANT: Make sure to uncheck "Exclude done with/no longer have"
6. Now, click export above this tab
7. Go back into the "More filter options" Tab and click "Achievements Not Won"
8. Click export again
9. Go to your Downloads Folder on your computer and rename these files.
   - The _listitems file should be renamed to -> unlocked.csv & the _lockedlistitems file should be renamed to -> locked.csv

### 2. Required CSV Format

Your CSV files should include these columns (TrueAchievements exports should have them automatically):

**Required columns:**
- `GameName` - Name of the game
- `Gamerscore` - Gamerscore value of the achievement
- `TAScore` - TrueAchievements score
- `TARatio` - TA Ratio (TA Score / Gamerscore)
- `DLCName` - DLC name (empty if base game achievement)
- `UnlockDate` - Date unlocked (for unlocked.csv only)
- `Unachieveable` - Whether achievement is unachievable (for locked.csv only)

**Note:** Column names are case-sensitive. If your export uses different column names, you may need to rename them.

### 3. Place Files in Project

1. Create a `data` folder in the project root (if it doesn't exist)
2. Copy your CSV files to:
   - `data/unlocked.csv`
   - `data/locked.csv`

### 4. Run the Program

Open a terminal/command prompt in the project directory and run:

```bash
python rank_next.py
```

The program will silently generate:
- `main_stats.json` - Main dashboard data
- `dlc_data.json` - DLC checklist data

### 5. View Your Dashboard

Open `page.html` in any web browser to see your dashboard!

## Troubleshooting

**"FileNotFoundError: data/unlocked.csv"**
- Make sure the `data/` folder exists
- Check that files are named exactly `unlocked.csv` and `locked.csv` (case-sensitive)
- Verify files are in the `data/` folder, not the root directory

**"KeyError" or missing column errors**
- Verify your CSV files have all required columns
- Check that column names match exactly (case-sensitive)
- TrueAchievements exports should include all required columns automatically

**Numbers seem wrong**
- Your CSV export might be incomplete (TrueAchievements may limit export size)
- Try re-exporting your data from TrueAchievements
- Check that both unlocked and locked exports are complete

**HTML shows "Loading..." forever**
- Make sure you ran `python rank_next.py` first
- Check that `main_stats.json` and `dlc_data.json` exist in the project root
- Open browser console (F12) to see any JavaScript errors

## Need Help?

If you encounter issues:
1. Check that your Python version is 3.6 or higher: `python --version`
2. Verify your CSV files are valid (open them in Excel/Notepad to check)
3. Make sure all files are in the correct locations
