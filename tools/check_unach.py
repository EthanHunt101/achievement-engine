import csv
from pathlib import Path

def safe_int(x):
    try:
        return int(str(x).replace(',', '').strip())
    except Exception:
        return 0

def is_truthy(x):
    s = str(x).strip().lower()
    return s in ('1','true','yes','y','t')

PATH = Path('data/locked.csv')
if not PATH.exists():
    print('missing data/locked.csv')
    raise SystemExit(1)

per_game = {}
rows = 0
with PATH.open('r', encoding='utf-8-sig', newline='') as f:
    r = csv.DictReader(f)
    for row in r:
        rows += 1
        game = (row.get('GameName') or '').strip()
        gs = safe_int(row.get('Gamerscore', 0))
        unach = is_truthy(row.get('Unachieveable',''))
        g = per_game.setdefault(game, {'unach_count':0,'unach_gs':0,'locked_count':0,'locked_gs':0})
        g['locked_count'] += 1
        g['locked_gs'] += gs
        if unach:
            g['unach_count'] += 1
            g['unach_gs'] += gs

# totals
total_unach = sum(g['unach_count'] for g in per_game.values())
total_unach_gs = sum(g['unach_gs'] for g in per_game.values())
print(f"rows={rows}")
print(f"per_game_count={len(per_game)}")
print(f"total_unach_count={total_unach}")
print(f"total_unach_gs={total_unach_gs}")
print('\nTop games by unachievable count:')
for game, g in sorted(per_game.items(), key=lambda kv: kv[1]['unach_count'], reverse=True)[:30]:
    if g['unach_count']>0:
        print(f"- {game}: {g['unach_count']} unachievable ({g['unach_gs']} GS) of {g['locked_count']} locked total")

print('\nTop games by unachievable GS:')
for game, g in sorted(per_game.items(), key=lambda kv: kv[1]['unach_gs'], reverse=True)[:30]:
    if g['unach_gs']>0:
        print(f"- {game}: {g['unach_gs']} GS from {g['unach_count']} unachievable ({g['locked_count']} locked total)")
