"""The scaling gates' check ratios, recomputed from their ncheck.jsonl / gate.jsonl on the analysis branch (report only).

A gate's check ratio is (A's ms per decision) / (B's ms per decision) over the same games, with A and B on opposite
decks in a non-mirror pairing. Per side: games, decisions per game, N (iterations per decision), ms per decision;
for a full gate also sd_20_pairs, the SD of the ratio a 20-pair check would read on its games (a pair bootstrap, 4000
draws, random.Random(0)).

    python analysis/scaling/gate_ratios.py [REF] > OUT.json
"""
import json, random, subprocess, sys

REF = sys.argv[1] if len(sys.argv) > 1 else "origin/ccr-da4857cc-rkpgwr"


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True).stdout


def side(rs, mk, ik):
    ms = sum(s["total"] for r in rs for s in r[mk]); n = sum(s["n"] for r in rs for s in r[mk])
    games = sum(len(r[mk]) for r in rs)
    it = sum(s["total"] for r in rs for s in r[ik])
    return dict(games=games, decisions_per_game=round(n / games, 2), N=round(it / n, 1), ms_per_decision=round(ms / n, 2))


out = {}
for f in git("ls-tree", "-r", "--name-only", REF, "analysis/gates/scaling/").split():
    if "/nm" not in f or not f.endswith(("/ncheck.jsonl", "/gate.jsonl")):
        continue
    d = f.rsplit("/", 1)[0]
    chk = git("show", f"{REF}:{d}/check.json")
    if f.endswith("ncheck.jsonl") and not chk.strip():
        continue                                   # a check still running
    rs = [json.loads(l) for l in git("show", f"{REF}:{f}").splitlines() if l.strip()]
    a, b = side(rs, "ms", "iterations"), side(rs, "ms_b", "iterations_b")
    out[f.replace("analysis/gates/scaling/", "")] = dict(A=a, B=b, ratio=round(a["ms_per_decision"] / b["ms_per_decision"], 4),
        check_ratio=round(json.loads(chk)["check_ratio"], 4) if f.endswith("ncheck.jsonl") else None)
    if f.endswith("/gate.jsonl"):                  # what a 20-pair check would read on these games: a pair bootstrap
        per = [[sum(s["total"] for s in r[k]) for k in ("ms", "ms_b")] + [sum(s["n"] for s in r[k]) for k in ("ms", "ms_b")]
               for r in rs]
        rnd, qs = random.Random(0), []
        for _ in range(4000):
            smp = [per[rnd.randrange(len(per))] for _ in range(20)]
            t = [sum(x[i] for x in smp) for i in range(4)]
            qs.append((t[0] / t[2]) / (t[1] / t[3]))
        m = sum(qs) / len(qs)
        out[f.replace("analysis/gates/scaling/", "")]["sd_20_pairs"] = round((sum((q - m) ** 2 for q in qs) / len(qs)) ** 0.5, 4)
json.dump(out, sys.stdout, indent=1)
print()
