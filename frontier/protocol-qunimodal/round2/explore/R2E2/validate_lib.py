# Cross-check lib.unimodal_d against the ground-truth checker tools/uni on random instances (fit box).
import random, subprocess, sys
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
random.seed(1)
lines = []; mine = []
for _ in range(4000):
    r = random.randint(2, 9); k = random.randint(1, 7)
    a = sorted(random.randint(1, 25) for _ in range(k))
    b = random.randint(1, T6(r, a) + 3)
    lines.append(f"{r} {k} {' '.join(map(str,a))} {b}")
    mine.append(1 if unimodal_d(DS(r, a), b) else 0)
out = subprocess.run(['/tmp/claude-0/qu/tools/uni'], input='\n'.join(lines) + '\n', capture_output=True, text=True).stdout.split()
gt = list(map(int, out))
bad = sum(1 for x, y in zip(mine, gt) if x != y)
print("instances", len(gt), "mismatches", bad, "unimodal count", sum(gt))
