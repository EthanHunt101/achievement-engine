import csv
from collections import defaultdict
from pathlib import Path
import json


UNLOCKED_PATH = Path("data/unlocked.csv")
LOCKED_PATH   = Path("data/locked.csv")


# ====== SETTINGS YOU CAN TWEAK ======
INCLUDE_DLC = True                 # If False, ignore DLC achievements entirely
COUNT_UNACHIEVABLE_IN_TOTAL = True # If False, unachievable locked achs won't count against completion %
# ===================================

def safe_int(x, default=0):
    try:
        return int(str(x).replace(",", "").strip())
    except Exception:
        return default

def safe_float(x, default=None):
    try:
        s = str(x).strip()
        if s == "":
            return default
        return float(s)
    except Exception:
        return default

def is_truthy(x: str) -> bool:
    # handles: "1", "true", "TRUE", "Yes", etc.
    s = str(x).strip().lower()
    return s in ("1", "true", "yes", "y", "t")


def load_csv(path: Path, required: set):
    """Load a CSV file and validate required headers.

    Returns a list of rows (dicts).
    """
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name} CSV missing columns: {missing}. Found: {reader.fieldnames}")
        return list(reader)

def read_unlocked(games):
    required = {"GameName","Gamerscore","TAScore","TARatio","DLCName","UnlockDate"}
    rows = load_csv(UNLOCKED_PATH, required)

    for r in rows:
        game = (r.get("GameName") or "").strip()
        dlc_name = (r.get("DLCName") or "").strip()
        if (not INCLUDE_DLC) and dlc_name:
            continue

        gs = safe_int(r.get("Gamerscore", 0))
        ta = safe_int(r.get("TAScore", 0))
        ratio = safe_float(r.get("TARatio"))

        # Unlocked file is said to contain only unlocked achievements, but keep check anyway:
        if not str(r.get("UnlockDate","")).strip():
            continue

        g = games[game]
        g["earned_ach"] += 1
        g["earned_gs"] += gs
        g["earned_ta"] += ta
        if dlc_name:
            g["earned_dlc_ach"] += 1

        # Track ratios (optional)
        if ratio is not None:
            g["earned_ratios"].append(ratio)
        # store row for listing (try to find a title field)
        title = None
        for k in ("AchievementName", "AchievementTitle", "Name", "Title"):
            if k in r and str(r.get(k)).strip():
                title = str(r.get(k)).strip()
                break
        g.setdefault("earned_achievements", []).append({"ratio": ratio, "gamerscore": gs, "ta": ta, "dlc": dlc_name, "title": title, "row": r})

def read_locked(games):
    required = {"GameName","Gamerscore","TAScore","TARatio","DLCName","Unachieveable"}
    rows = load_csv(LOCKED_PATH, required)

    for r in rows:
        game = (r.get("GameName") or "").strip()
        dlc_name = (r.get("DLCName") or "").strip()
        if (not INCLUDE_DLC) and dlc_name:
            continue

        gs = safe_int(r.get("Gamerscore", 0))
        ta = safe_int(r.get("TAScore", 0))
        ratio = safe_float(r.get("TARatio"))

        '''
        Along with self unachievable games i am also going to manually enter some 
        here as they are discontinued hence can't be bought and completed anymore
        '''
        unach = is_truthy(r.get("Unachieveable","")) or (game == "Besiege (Windows)" )or (game == "Second Extinction")

        g = games[game]
        g["locked_ach_total"] += 1
        g["locked_gs_total"] += gs
        g["locked_ta_total"] += ta
        if dlc_name:
            g["locked_dlc_ach"] += 1

        '''
        Along with self unachievable games i am also going to manually enter some here as they are discontinued
        '''
        if unach:
            g["locked_ach_unach"] += 1
            g["locked_gs_unach"] += gs
            g["locked_ta_unach"] += ta
            if dlc_name:
                g["locked_dlc_unach"] += 1

        # Ratio opportunity: only consider achievable locked achievements
        if (not unach) and ratio is not None:
            g["locked_ratios_achievable"].append(ratio)
        # store locked achievement row (mark unachievable)
        title = None
        for k in ("AchievementName", "AchievementTitle", "Name", "Title"):
            if k in r and str(r.get(k)).strip():
                title = str(r.get(k)).strip()
                break
        g.setdefault("locked_achievements_all", []).append({"ratio": ratio, "gamerscore": gs, "ta": ta, "dlc": dlc_name, "title": title, "unachievable": unach, "row": r})
        if not unach:
            g.setdefault("locked_achievements_achievable", []).append({"ratio": ratio, "gamerscore": gs, "ta": ta, "dlc": dlc_name, "title": title, "row": r})

def get_game_info(game, g):
    """Extract game information for ranking. Games are ranked by number of remaining achievements (ascending)."""
    # Totals: earned + locked, optionally excluding unachievable
    # Compute remaining achievements/GS according to COUNT_UNACHIEVABLE_IN_TOTAL
    locked_ach_effective = g["locked_ach_total"]
    locked_gs_effective  = g["locked_gs_total"]

    if not COUNT_UNACHIEVABLE_IN_TOTAL:
        locked_ach_effective -= g["locked_ach_unach"]
        locked_gs_effective  -= g["locked_gs_unach"]

    # For completion percentage, always include unachievable locked GS as part
    # of the game's total (they are still a portion of the game's GS even if
    # you can't earn them). This affects the completion percent only.
    total_ach = g["earned_ach"] + max(0, locked_ach_effective)
    total_gs_for_completion = g["earned_gs"] + max(0, g["locked_gs_total"])

    if total_ach <= 0 or total_gs_for_completion <= 0:
        return None

    completion = g["earned_gs"] / total_gs_for_completion  # 0..1
    remaining_ach = max(0, locked_ach_effective)
    remaining_gs  = max(0, locked_gs_effective)

    # ✅ Don't recommend already-finished games
    if remaining_ach == 0:
        return None

    # Compute average locked TARatio for achievable locked achievements (for display only)
    ratios = g.get("locked_ratios_achievable", [])
    avg_ratio = (sum(ratios) / len(ratios)) if ratios else None

    return {
        "game": game,
        "completion": completion,
        "remaining_ach": remaining_ach,
        "remaining_gs": remaining_gs,
        "unach_ach": g["locked_ach_unach"],
        "dlc_remaining": g["locked_dlc_ach"],
        "avg_locked_ratio": avg_ratio,
        "earned_ach": g["earned_ach"],
        "total_ach": total_ach,
        "earned_gs": g["earned_gs"],
        "total_gs": total_gs_for_completion
    }





def export_main_stats(games, ranked, total_games, completed_games, total_gs_earned, total_gs_possible, 
                      total_ta_earned, total_ta_possible, overall_completion_pct, buckets, started_games,
                      blocked, dlc_only, output_path: Path):
    """Export main dashboard stats to JSON for HTML visualization."""
    
    # Prepare recommendations
    recommendations = []
    for r in ranked:
        recommendations.append({
            "game": r["game"],
            "completion": r["completion"] * 100,
            "remaining_ach": r["remaining_ach"],
            "remaining_gs": r["remaining_gs"],
            "avg_locked_ratio": r["avg_locked_ratio"],
            "unach_ach": r["unach_ach"],
            "dlc_remaining": r["dlc_remaining"],
            "earned_ach": r["earned_ach"],
            "total_ach": r["total_ach"],
            "earned_gs": r["earned_gs"],
            "total_gs": r["total_gs"]
        })
    
    # Prepare blocked games
    blocked_games = []
    total_unach_count = sum(x[1] for x in blocked) if blocked else 0
    total_unach_gs = sum(x[2] for x in blocked) if blocked else 0
    for game, count, gs_unach, total_locked in sorted(blocked, key=lambda x: x[1], reverse=True) if blocked else []:
        blocked_games.append({
            "game": game,
            "unach_count": count,
            "unach_gs": gs_unach,
            "total_locked": total_locked,
            "fully_blocked": (total_locked > 0 and count == total_locked)
        })
    
    # Prepare DLC-only games
    dlc_only_games = []
    for game, cnt in sorted(dlc_only, key=lambda x: x[1], reverse=True) if dlc_only else []:
        dlc_only_games.append({
            "game": game,
            "dlc_achievements_remaining": cnt
        })
    
    # Prepare completion buckets (must match bucket_labels in main())
    completion_buckets = []
    for label in ["0-19%", "20-39%", "40-59%", "60-79%", "80-94%", "95-99%", "100%"]:
        cnt = buckets.get(label, 0)
        pct = (cnt / started_games * 100) if started_games > 0 else 0.0
        completion_buckets.append({
            "label": label,
            "count": cnt,
            "percentage": pct
        })
    
    # Prepare all games list (including completed ones)
    all_games_list = []
    for game_name, g in sorted(games.items()):
        # Calculate stats for this game
        locked_gs_effective = g["locked_gs_total"]
        locked_ach_effective = g["locked_ach_total"]
        locked_ta_effective = g["locked_ta_total"]
        
        if not COUNT_UNACHIEVABLE_IN_TOTAL:
            locked_gs_effective -= g["locked_gs_unach"]
            locked_ta_effective -= g["locked_ta_unach"]
            locked_ach_effective -= g["locked_ach_unach"]
        
        total_gs = g["earned_gs"] + max(0, locked_gs_effective)
        total_ta = g["earned_ta"] + max(0, locked_ta_effective)
        remaining_ach = max(0, locked_ach_effective)
        
        # Only include games with some data
        if g.get("earned_gs", 0) > 0 or g.get("earned_ach", 0) > 0 or total_gs > 0:
            completion_pct = (g["earned_gs"] / total_gs * 100) if total_gs > 0 else 0.0
            all_games_list.append({
                "game": game_name,
                "earned_gs": g["earned_gs"],
                "earned_ta": g["earned_ta"],
                "earned_ach": g["earned_ach"],
                "total_gs": total_gs,
                "total_ta": total_ta,
                "total_ach": g["earned_ach"] + max(0, locked_ach_effective),
                "remaining_ach": remaining_ach,
                "remaining_gs": max(0, locked_gs_effective),
                "completion_pct": completion_pct,
                "is_completed": remaining_ach == 0,
                "locked_unach_ach": g["locked_ach_unach"],
                "locked_unach_gs": g["locked_gs_unach"]
            })
    
    # Calculate overall TA ratios
    overall_ta_ratio_earned = (total_ta_earned / total_gs_earned) if total_gs_earned > 0 else None
    overall_ta_ratio_possible = (total_ta_possible / total_gs_possible) if total_gs_possible > 0 else None
    
    export_data = {
        "profile_summary": {
            "total_games": total_games,
            "completed_games": completed_games,
            "total_gs_earned": total_gs_earned,
            "total_gs_possible": total_gs_possible,
            "gs_completion_pct": overall_completion_pct,
            "total_ta_earned": total_ta_earned,
            "total_ta_possible": total_ta_possible,
            "ta_completion_pct": (total_ta_earned / total_ta_possible * 100) if total_ta_possible > 0 else 0.0,
            "overall_ta_ratio_earned": overall_ta_ratio_earned,
            "overall_ta_ratio_possible": overall_ta_ratio_possible,
            "started_games": started_games
        },
        "completion_buckets": completion_buckets,
        "recommendations": recommendations,
        "blocked_games": {
            "total_unach_count": total_unach_count,
            "total_unach_gs": total_unach_gs,
            "games": blocked_games
        },
        "dlc_only_games": dlc_only_games,
        "all_games": all_games_list,
        "settings": {
            "include_dlc": INCLUDE_DLC,
            "count_unachievable_in_total": COUNT_UNACHIEVABLE_IN_TOTAL
        }
    }
    
    # Write to file
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    return export_data

def export_dlc_data(games, output_path: Path):
    """Export DLC completion data to JSON for HTML visualization.
    
    Returns a dictionary with:
    - dlcs: list of DLCs grouped by game
    - summary: overall stats
    """
    dlc_data = {}
    game_stats_dict = {}
    summary = {
        "total_dlcs": 0,
        "completed_dlcs": 0,
        "total_dlc_achievements": 0,
        "completed_dlc_achievements": 0,
        "total_dlc_gamerscore": 0,
        "completed_dlc_gamerscore": 0,
        "total_dlc_tascore": 0,
        "completed_dlc_tascore": 0
    }
    
    for game_name, game_data in games.items():
        # Collect all DLCs for this game
        dlcs_for_game = {}
        
        # Process earned achievements
        for ach in game_data.get("earned_achievements", []):
            dlc_name = ach.get("dlc", "").strip()
            if not dlc_name:
                continue
            
            if dlc_name not in dlcs_for_game:
                dlcs_for_game[dlc_name] = {
                    "game": game_name,
                    "dlc_name": dlc_name,
                    "earned_ach": 0,
                    "earned_gs": 0,
                    "earned_ta": 0,
                    "locked_ach": 0,
                    "locked_gs": 0,
                    "locked_ta": 0,
                    "locked_unach_ach": 0,
                    "locked_unach_gs": 0,
                    "earned_ratios": [],
                    "locked_ratios": []
                }
            
            dlc = dlcs_for_game[dlc_name]
            dlc["earned_ach"] += 1
            dlc["earned_gs"] += ach.get("gamerscore", 0)
            dlc["earned_ta"] += ach.get("ta", 0)
            if ach.get("ratio") is not None:
                dlc["earned_ratios"].append(ach.get("ratio"))
        
        # Process locked achievements
        for ach in game_data.get("locked_achievements_all", []):
            dlc_name = ach.get("dlc", "").strip()
            if not dlc_name:
                continue
            
            if dlc_name not in dlcs_for_game:
                dlcs_for_game[dlc_name] = {
                    "game": game_name,
                    "dlc_name": dlc_name,
                    "earned_ach": 0,
                    "earned_gs": 0,
                    "earned_ta": 0,
                    "locked_ach": 0,
                    "locked_gs": 0,
                    "locked_ta": 0,
                    "locked_unach_ach": 0,
                    "locked_unach_gs": 0,
                    "earned_ratios": [],
                    "locked_ratios": []
                }
            
            dlc = dlcs_for_game[dlc_name]
            dlc["locked_ach"] += 1
            dlc["locked_gs"] += ach.get("gamerscore", 0)
            dlc["locked_ta"] += ach.get("ta", 0)
            if ach.get("ratio") is not None:
                dlc["locked_ratios"].append(ach.get("ratio"))
            
            if ach.get("unachievable", False):
                dlc["locked_unach_ach"] += 1
                dlc["locked_unach_gs"] += ach.get("gamerscore", 0)
        
        # Calculate completion status for each DLC
        for dlc_name, dlc in dlcs_for_game.items():
            total_ach = dlc["earned_ach"] + dlc["locked_ach"]
            total_gs = dlc["earned_gs"] + dlc["locked_gs"]
            
            # Effective remaining (excluding unachievable if configured)
            effective_locked_ach = dlc["locked_ach"]
            if not COUNT_UNACHIEVABLE_IN_TOTAL:
                effective_locked_ach -= dlc["locked_unach_ach"]
            
            total_ta = dlc["earned_ta"] + dlc["locked_ta"]
            
            # Calculate average TA ratios
            all_earned_ratios = dlc.get("earned_ratios", [])
            all_locked_ratios = dlc.get("locked_ratios", [])
            avg_earned_ratio = (sum(all_earned_ratios) / len(all_earned_ratios)) if all_earned_ratios else None
            avg_locked_ratio = (sum(all_locked_ratios) / len(all_locked_ratios)) if all_locked_ratios else None
            avg_overall_ratio = None
            all_ratios = all_earned_ratios + all_locked_ratios
            if all_ratios:
                avg_overall_ratio = sum(all_ratios) / len(all_ratios)
            
            dlc["total_ach"] = total_ach
            dlc["total_gs"] = total_gs
            dlc["total_ta"] = total_ta
            dlc["remaining_ach"] = max(0, effective_locked_ach)
            dlc["remaining_gs"] = max(0, dlc["locked_gs"] - (dlc["locked_unach_gs"] if not COUNT_UNACHIEVABLE_IN_TOTAL else 0))
            dlc["completion_pct"] = (dlc["earned_gs"] / total_gs * 100) if total_gs > 0 else 0.0
            dlc["is_completed"] = (dlc["remaining_ach"] == 0) and (total_ach > 0)
            dlc["avg_earned_ratio"] = avg_earned_ratio
            dlc["avg_locked_ratio"] = avg_locked_ratio
            dlc["avg_overall_ratio"] = avg_overall_ratio
            
            # Add to summary
            summary["total_dlcs"] += 1
            if dlc["is_completed"]:
                summary["completed_dlcs"] += 1
            summary["total_dlc_achievements"] += total_ach
            summary["completed_dlc_achievements"] += dlc["earned_ach"]
            summary["total_dlc_gamerscore"] += total_gs
            summary["completed_dlc_gamerscore"] += dlc["earned_gs"]
            summary["total_dlc_tascore"] += total_ta
            summary["completed_dlc_tascore"] += dlc["earned_ta"]
        
        # Store DLCs for this game and calculate game-level stats
        if dlcs_for_game:
            if game_name not in dlc_data:
                dlc_data[game_name] = []
            dlc_list = list(dlcs_for_game.values())
            dlc_data[game_name] = dlc_list
            
            # Calculate game-level DLC stats
            game_dlc_stats = {
                "total_dlcs": len(dlc_list),
                "completed_dlcs": sum(1 for d in dlc_list if d.get("is_completed", False)),
                "total_gs": sum(d.get("total_gs", 0) for d in dlc_list),
                "earned_gs": sum(d.get("earned_gs", 0) for d in dlc_list),
                "total_ta": sum(d.get("total_ta", 0) for d in dlc_list),
                "earned_ta": sum(d.get("earned_ta", 0) for d in dlc_list),
            }
            # Calculate average ratio for this game's DLCs
            # Use earned ratio (what you've achieved) instead of overall ratio
            all_game_earned_ratios = []
            all_game_overall_ratios = []
            for d in dlc_list:
                if d.get("avg_earned_ratio") is not None:
                    all_game_earned_ratios.append(d.get("avg_earned_ratio"))
                if d.get("avg_overall_ratio") is not None:
                    all_game_overall_ratios.append(d.get("avg_overall_ratio"))
            game_dlc_stats["avg_earned_ratio"] = (sum(all_game_earned_ratios) / len(all_game_earned_ratios)) if all_game_earned_ratios else None
            game_dlc_stats["avg_overall_ratio"] = (sum(all_game_overall_ratios) / len(all_game_overall_ratios)) if all_game_overall_ratios else None
            # Default to earned ratio for display
            game_dlc_stats["avg_ratio"] = game_dlc_stats["avg_earned_ratio"]
            
            # Store game stats
            game_stats_dict[game_name] = game_dlc_stats
    
    # Convert to list format for easier HTML consumption
    all_dlcs = []
    for game_name in sorted(dlc_data.keys()):
        for dlc in sorted(dlc_data[game_name], key=lambda x: x["dlc_name"]):
            all_dlcs.append(dlc)
    
    # Calculate overall game stats (not just DLC)
    overall_stats = {
        "total_games": len(games),
        "total_earned_gs": sum(g.get("earned_gs", 0) for g in games.values()),
        "total_earned_ta": sum(g.get("earned_ta", 0) for g in games.values()),
        "total_locked_gs": sum(g.get("locked_gs_total", 0) for g in games.values()),
        "total_locked_ta": sum(g.get("locked_ta_total", 0) for g in games.values()),
    }
    overall_stats["total_gs"] = overall_stats["total_earned_gs"] + overall_stats["total_locked_gs"]
    overall_stats["total_ta"] = overall_stats["total_earned_ta"] + overall_stats["total_locked_ta"]
    
    # Calculate overall average TA ratio
    all_earned_ratios = []
    all_locked_ratios = []
    for g in games.values():
        all_earned_ratios.extend(g.get("earned_ratios", []))
        all_locked_ratios.extend(g.get("locked_ratios_achievable", []))
    
    overall_stats["avg_earned_ratio"] = (sum(all_earned_ratios) / len(all_earned_ratios)) if all_earned_ratios else None
    overall_stats["avg_locked_ratio"] = (sum(all_locked_ratios) / len(all_locked_ratios)) if all_locked_ratios else None
    all_ratios_combined = all_earned_ratios + all_locked_ratios
    overall_stats["avg_overall_ratio"] = (sum(all_ratios_combined) / len(all_ratios_combined)) if all_ratios_combined else None
    
    export_data = {
        "summary": summary,
        "overall_stats": overall_stats,
        "dlcs": all_dlcs,
        "games": {game: dlcs for game, dlcs in dlc_data.items() if game != "game_stats"},
        "game_stats": game_stats_dict
    }
    
    # Write to file
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    return export_data

def main():
    # Use default settings (no CLI arguments)
    global INCLUDE_DLC, COUNT_UNACHIEVABLE_IN_TOTAL

    if not UNLOCKED_PATH.exists():
        raise FileNotFoundError(f"Missing {UNLOCKED_PATH} (your unlocked export).")
    if not LOCKED_PATH.exists():
        raise FileNotFoundError(f"Missing {LOCKED_PATH} (your locked export).")

    games = defaultdict(lambda: {
        "earned_ach": 0, "earned_gs": 0, "earned_ta": 0,
        "earned_dlc_ach": 0,
        "locked_ach_total": 0, "locked_gs_total": 0, "locked_ta_total": 0,
        "locked_dlc_ach": 0,
        "locked_ach_unach": 0, "locked_gs_unach": 0, "locked_ta_unach": 0,
        "locked_dlc_unach": 0,
        "earned_ratios": [],
        "locked_ratios_achievable": []
    })

    read_unlocked(games)
    read_locked(games)

    # ===== PROFILE-LEVEL STATS =====
    # Sum ALL earned GS/TA directly from unlocked.csv to get true totals
    # IMPORTANT: Count ALL achievements regardless of DLC settings for total earned
    # (DLC filtering only affects recommendations, not your total earned stats)
    total_gs_earned = 0
    total_ta_earned = 0
    try:
        required = {"GameName","Gamerscore","TAScore","TARatio","DLCName","UnlockDate"}
        unlocked_rows = load_csv(UNLOCKED_PATH, required)
        for r in unlocked_rows:
            unlock_date = str(r.get("UnlockDate","")).strip()
            if not unlock_date:
                continue
            # Count ALL achievements for total earned (don't filter DLC here)
            total_gs_earned += safe_int(r.get("Gamerscore", 0))
            total_ta_earned += safe_int(r.get("TAScore", 0))
    except Exception as e:
        # Fallback to games dictionary if CSV read fails
        total_gs_earned = sum(g.get("earned_gs", 0) for g in games.values())
        total_ta_earned = sum(g.get("earned_ta", 0) for g in games.values())
    
    total_games = 0
    completed_games = 0
    total_gs_possible = 0
    total_ta_possible = 0

    for game, g in games.items():
        # Effective locked GS (respecting unachievable setting)
        locked_gs_effective = g["locked_gs_total"]
        locked_ach_effective = g["locked_ach_total"]
        locked_ta_effective = g["locked_ta_total"]

        if not COUNT_UNACHIEVABLE_IN_TOTAL:
            locked_gs_effective -= g["locked_gs_unach"]
            locked_ta_effective -= g["locked_ta_unach"]
            locked_ach_effective -= g["locked_ach_unach"]

        # For possible totals, use earned + locked (or just earned if no locked)
        total_gs = g["earned_gs"] + max(0, locked_gs_effective)
        total_ta = g["earned_ta"] + max(0, locked_ta_effective)
        remaining_ach = max(0, locked_ach_effective)

        # Count all games with any earned achievements
        if g.get("earned_gs", 0) > 0 or g.get("earned_ach", 0) > 0:
            total_games += 1
            if remaining_ach == 0:
                completed_games += 1
            
            # Add to possible totals (use earned_gs as minimum if total_gs is somehow 0)
            total_gs_possible += max(total_gs, g.get("earned_gs", 0))
            total_ta_possible += max(total_ta, g.get("earned_ta", 0))

    overall_completion_pct = (
        (total_gs_earned / total_gs_possible) * 100
        if total_gs_possible > 0 else 0.0
    )

    # Completion buckets for profile overview (only consider started games)
    # Evenly spread buckets: 0-19, 20-39, 40-59, 60-79, 80-94, 95-99, 100
    bucket_labels = ["0-19%", "20-39%", "40-59%", "60-79%", "80-94%", "95-99%", "100%"]
    buckets = {label: 0 for label in bucket_labels}
    started_games = 0

    for game, g in games.items():
        locked_gs_effective = g["locked_gs_total"]
        locked_ach_effective = g["locked_ach_total"]
        if not COUNT_UNACHIEVABLE_IN_TOTAL:
            locked_gs_effective -= g["locked_gs_unach"]
            locked_ach_effective -= g["locked_ach_unach"]

        total_gs = g["earned_gs"] + max(0, locked_gs_effective)
        if total_gs <= 0:
            continue
        started_games += 1
        pct = (g["earned_gs"] / total_gs) * 100
        # place into bucket
        if pct >= 100:
            buckets["100%"] += 1
        elif pct >= 95:
            buckets["95-99%"] += 1
        elif pct >= 80:
            buckets["80-94%"] += 1
        elif pct >= 60:
            buckets["60-79%"] += 1
        elif pct >= 40:
            buckets["40-59%"] += 1
        elif pct >= 20:
            buckets["20-39%"] += 1
        else:
            buckets["0-19%"] += 1

    ranked = []
    for game, g in games.items():
        result = get_game_info(game, g)
        if result:
            ranked.append(result)

    # Sort by remaining achievements (ascending) - fewer achievements = higher priority
    ranked.sort(key=lambda x: x["remaining_ach"])
        
    # Games with any unachievable achievements (for export)
    blocked = []
    for game, g in games.items():
        if g["locked_ach_unach"] > 0:
            blocked.append((game, g["locked_ach_unach"], g["locked_gs_unach"], g["locked_ach_total"]))

    # Games with only DLC remaining (for export)
    dlc_only = []
    for game, g in games.items():
        if g["locked_ach_total"] <= 0:
            continue
        locked_ach_effective = g["locked_ach_total"]
        if not COUNT_UNACHIEVABLE_IN_TOTAL:
            locked_ach_effective -= g["locked_ach_unach"]

        dlc_remaining_effective = g["locked_dlc_ach"] - (g["locked_dlc_unach"] if not COUNT_UNACHIEVABLE_IN_TOTAL else 0)
        if locked_ach_effective > 0 and locked_ach_effective == dlc_remaining_effective:
            dlc_only.append((game, locked_ach_effective))

    # Export JSON files for HTML pages
    export_main_path = Path("main_stats.json")
    export_dlc_path = Path("dlc_data.json")
    
    # Export main stats to JSON
    export_main_stats(games, ranked, total_games, completed_games, total_gs_earned, total_gs_possible,
                    total_ta_earned, total_ta_possible, overall_completion_pct, buckets, started_games,
                    blocked, dlc_only, Path(export_main_path))
    
    # Export DLC data to JSON
    export_dlc_data(games, Path(export_dlc_path))


if __name__ == "__main__":
    main()
