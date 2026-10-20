"""Pre-registered N update after a calibration round (README "门里校准").

N_new = round(N_cal + (B_ms - A_ms) / s_in), s_in = s_fit * A_ms / F(N_cal), F(N) = a + s_fit * N (rerun/fit.sh's
least-squares line). Only a deck whose ratio is outside 0.95-1.05 is changed.
"""
import re
import sys

FIT = {"ramp-t": (42.887, 0.486), "nemesis-t": (55.974, 0.5607)}
ratio_file, n_ramp, n_nem = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
n_cal = {"ramp-t": n_ramp, "nemesis-t": n_nem}
for line in open(ratio_file):
    m = re.match(r"(\S+): A ([\d.]+) ms \(\d+\) / B ([\d.]+) ms \(\d+\) = ([\d.]+)", line)
    deck, a_ms, b_ms, r = m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4))
    a, s = FIT[deck]
    n = n_cal[deck]
    s_in = s * a_ms / (a + s * n)
    if 0.95 <= r <= 1.05:
        print(f"{deck}: ratio {r:.3f} in band, N stays {n}")
    else:
        print(f"{deck}: ratio {r:.3f} out of band; s_in {s_in:.4f} ms/N; N {n} -> {round(n + (b_ms - a_ms) / s_in)}")
