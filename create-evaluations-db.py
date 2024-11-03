import json
import sys

n = 0
for line in sys.stdin:
    obj = json.loads(line)
    fen = obj['fen']
    depths = [o['depth'] for o in obj['evals']]
    assert depths[0] >= max(depths)
    best_pv = obj['evals'][0]['pvs'][0]
    if 'mate' in best_pv:
        if best_pv['mate'] > 0:
            ev = 10000 - best_pv['mate']
        else:
            ev = -10000 - best_pv['mate']
    elif 'cp' in best_pv:
        ev = best_pv['cp']
    sys.stdout.write(f"{fen}\t{ev}\n")
    n += 1
    if n % 1000000 == 0:
        sys.stderr.write(f"read {n} evaluations...\n")

