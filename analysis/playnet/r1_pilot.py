"""R1 pilot's answers (README "Pilot"): the spread of the true sibling differences, how often the teacher's first is
the worse, how strongly paired playouts agree, and whether the hand-written score orders the two children as d does.

d is the mover's mean result over the m playouts from the teacher's first move minus that from its second (win-rate
points). Per decision, d's own noise is SE^2 = var(d_j) / m over the paired playouts j; over decisions, the true d's
variance is var(d) - mean(SE^2), and with a normal true d ~ N(mu, tau^2): P(d < 0) = Phi(-mu / tau), and the expected
gain of choosing the better of the two each time = E[max(0, -d)] = tau phi(mu / tau) - mu Phi(-mu / tau). Intervals by
bootstrap over decisions (2000 draws, seed fixed).

    python analysis/playnet/r1_pilot.py runs/r1/pilot.jsonl [--out analysis/playnet/pilot.json]

Condition: 对手卡表已知（牌序、手牌未知）.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict

import numpy as np

CLASSES = ("forest", "sword", "rune", "dragon", "abyss", "haven", "portal")


def load(path: str) -> list:
    rows = []
    for text in open(path):
        r = json.loads(text)
        if r.get("results") is not None:
            rows.append(r)
    return rows


def _phi(x: float) -> float:
    return math.exp(-x * x / 2) / math.sqrt(2 * math.pi)


def _Phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def stats(d: np.ndarray, se2: np.ndarray) -> dict:
    mu = float(d.mean())
    tau2 = float(d.var(ddof=1) - se2.mean())
    tau = math.sqrt(tau2) if tau2 > 0 else 0.0
    if tau > 0:
        p_wrong = _Phi(-mu / tau)
        gain = tau * _phi(mu / tau) - mu * _Phi(-mu / tau)
    else:
        p_wrong, gain = float(mu < 0), max(0.0, -mu)
    return {"mu": mu, "tau": tau, "p_wrong": p_wrong, "gain": gain, "noise": float(math.sqrt(se2.mean()))}


def summarize(rows: list, boot: int = 2000, seed: int = 85960001) -> dict:
    R1 = np.array([r["results"][0] for r in rows], float)
    R2 = np.array([r["results"][1] for r in rows], float)
    m = R1.shape[1]
    D = R1 - R2
    d = D.mean(axis=1)
    se2 = D.var(axis=1, ddof=1) / m
    out = {"decisions": len(rows), "m": m, **stats(d, se2)}
    rng = np.random.default_rng(seed)
    bs = defaultdict(list)
    for _ in range(boot):
        k = rng.integers(0, len(rows), len(rows))
        for key, v in stats(d[k], se2[k]).items():
            bs[key].append(v)
    out["ci95"] = {key: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for key, v in bs.items()}
    # Paired playouts: the correlation within decisions (each decision's own mean taken out) and overall.
    w1, w2 = R1 - R1.mean(axis=1, keepdims=True), R2 - R2.mean(axis=1, keepdims=True)
    den = math.sqrt(float((w1 ** 2).sum() * (w2 ** 2).sum()))
    out["corr_within"] = float((w1 * w2).sum() / den) if den > 0 else None
    out["corr_all"] = float(np.corrcoef(R1.ravel(), R2.ravel())[0, 1])
    out["identical_pairs"] = float((R1 == R2).mean())
    # The hand-written score's order against d's, where d is clear.
    hand = np.array([r["hand"][0] - r["hand"][1] for r in rows])
    se = np.sqrt(se2)
    clear = (se > 0) & (np.abs(d) > 2 * se) | (se == 0) & (d != 0)
    agree = np.sign(hand[clear]) == np.sign(d[clear])
    out["clear"] = int(clear.sum())
    out["clear_teacher_first_better"] = int((d[clear] > 0).sum())
    out["hand_agrees_clear"] = float(agree.mean()) if clear.any() else None
    out["hand_ties_clear"] = int((hand[clear] == 0).sum())
    out["hand_agrees_all_nonzero"] = float((np.sign(hand) == np.sign(d))[(d != 0) & (hand != 0)].mean())
    out["visits_first"] = float(np.mean([r["visits"][0] for r in rows]))
    out["cpu_per_playout"] = float(np.mean([r["cpu"] for r in rows]) / (2 * m))
    # By the mover's class, by the game's stage, by whether either move ends the turn.
    groups = defaultdict(list)
    for j, r in enumerate(rows):
        name = (r.get("names") or ["?", "?"])[r["mover"]] or "?"
        cls = next((c for c in CLASSES if c in name.lower()), "?")
        groups["class:" + cls].append(j)
        groups["stage:" + ("early" if r["turn"] <= 8 else "mid" if r["turn"] <= 16 else "late")].append(j)
        kinds = {mv.get("type") for mv in r["moves"]}
        groups["endturn:" + ("yes" if "EndTurn" in kinds else "no")].append(j)
    out["by"] = {}
    for key in sorted(groups):
        k = np.array(groups[key])
        if len(k) >= 20:
            out["by"][key] = {"n": len(k), **{a: round(b, 4) for a, b in stats(d[k], se2[k]).items()}}
    out["condition"] = "对手卡表已知（牌序、手牌未知）"
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path")
    ap.add_argument("--out")
    args = ap.parse_args()
    s = summarize(load(args.path))
    text = json.dumps(s, indent=1, ensure_ascii=False)
    print(text)
    if args.out:
        open(args.out, "w").write(text + "\n")


if __name__ == "__main__":
    main()
