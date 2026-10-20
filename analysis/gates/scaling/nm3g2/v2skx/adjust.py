"""Pre-registered N update after the calibration round (README "NM3 第 2 代直接对 v2skx").

If the geometric mean of the two in-gate same-deck ratios is within 0.90-1.10, the N stay. Otherwise both decks get
N_new = round(N_cal * (1 + 2 * (B_ms / A_ms - 1))) (elasticity 0.5), and the formal gate opens without another round.
"""
import math
import re
import sys

ratio_file, n_cal = sys.argv[1], {"elf-t": int(sys.argv[2]), "nemesis-t": int(sys.argv[3])}
rows = []
for line in open(ratio_file):
    m = re.match(r"(\S+): A ([\d.]+) ms \(\d+\) / B ([\d.]+) ms \(\d+\) = ([\d.]+)", line)
    rows.append((m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4))))
g = math.sqrt(rows[0][3] * rows[1][3])
ok = 0.90 <= g <= 1.10
print(f"geometric mean {g:.3f}: {'in band, N stay' if ok else 'out of band, both decks change'}")
for deck, a_ms, b_ms, r in rows:
    n = n_cal[deck]
    print(f"{deck}: ratio {r:.3f}; N {n} -> {n if ok else round(n * (1 + 2 * (b_ms / a_ms - 1)))}")
