"""Phase-0: task spec §3 CR steps, steady win rate per bin, and a two-player noise simulation.
    python analysis/ladder/tools/cr_sim.py
(An inference from the rules, not games.)"""
import random, statistics as S
def delta(d, won):
    """Points for the side with gap d = mine - theirs, by task spec §3 (integer)."""
    if d > 175: return 8 if won else -24
    if d < -175: return 24 if won else -8
    k = abs(d) // 25
    if d >= 0: return (16 - k) if won else -(16 + k)
    return (16 + k) if won else -(16 - k)
# zero-sum check over all integer gaps
assert all(delta(d, True) == -delta(-d, False) and delta(d, False) == -delta(-d, True) for d in range(-400, 401))
print("steady win rate by bin (spec §3):")
for k in range(8):
    print(f"  gap {25*k:3d}-{25*k+24:3d}: win +{16-k}, loss -{16+k}, steady {100*(16+k)/32:.3f}%")
print("  gap >175: +8/-24, steady 75%")
rng = random.Random(20261121)
print("two players, A wins with prob p; mean gap after burn-in (noise-smoothed):")
for p in [0.50,0.51,0.52,0.53,0.55,0.57,0.60,0.62,0.65,0.68,0.70,0.72,0.74]:
    a, b, gaps = 1500, 1500, []
    for t in range(400000):
        won = rng.random() < p
        da = delta(a - b, won); a += da; b -= da
        if t > 20000: gaps.append(a - b)
    m = S.mean(gaps)
    print(f"  p={p:.2f}: mean gap {m:6.1f}  ({m/(100*(p-0.5)) if p>0.5 else float('nan'):.2f} CR per pp)  sd {S.pstdev(gaps):.1f}")
