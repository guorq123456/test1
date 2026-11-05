"""The move prior for one of the four new-PC bot heroes after g3 (PC-PILOTS.md), as PRIOR-HAVEN.md, for Windows.

    py analysis/process/pilot_prior_win.py DECK WORKERS        e.g.  py analysis/process/pilot_prior_win.py forest 3

Run from the repo root (with PYTHONPATH set to it); resumable. Steps, all in g1's run directory runs/pilot-DECK-bot-g1:
  1. init: g2's net on g3's confirmation deals (base + 6000) at g3's equal-CPU N; init = g3 if g3 - g2 >= 0, else g2;
  2. the hero's decisions in the gen-2 and gen-3 self-play (setpolicy_named.py encode);
  3. fit from the init net: --tau 0.5 --ftz --epochs 35;
  4. the arm +puct=<prior>:2:1 on the init net: time match (base + 9800), gate on g3's deals, an equal-CPU rerun;
  5. the prior's equal-CPU row paired with the init net's equal-CPU row on the same deals.
"""
import glob
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time

HEROES = {"forest": ("bot/T1-FOREST-1", 86960000), "sword": ("bot/T1-SWORD-1", 87020000),
          "dragon": ("bot/T3-DRAGON-1", 87080000), "abyss": ("bot/T1-ABYSS-1", 87140000)}
DECK, W = sys.argv[1], int(sys.argv[2])
DRY = len(sys.argv) > 3
assert DECK in HEROES, "DECK forest|sword|dragon|abyss"
if os.name == "nt":
    import ctypes
    k = ctypes.windll.kernel32
    k.SetPriorityClass(k.GetCurrentProcess(), 0x4000)   # below normal; children inherit
HERO, BANK = HEROES[DECK]
FIELD = "analysis/pilot/fields/bot-frozen7.txt"
RUN = f"runs/pilot-{DECK}-bot-g1"
L = f"{RUN}/logs"
SELF2, SELF3 = BANK + 3000, BANK + 5000
GATE3, TIME = BANK + 6000, BANK + 9800
MODELS = "analysis/scaling/models"
PRI = f"{MODELS}/prior-pilot-{DECK}-bot-ft-t05.npz"
ENV = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONUTF8="1")
LOG = open(f"{L}/prior-{DECK}-bot.log", "a", encoding="utf-8")  # noqa: SIM115


def say(s):
    LOG.write(f"== {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {s}\n")
    LOG.flush()


def run(args, out=None):
    say(" ".join(args))
    if DRY:
        return
    f = open(out, "w", encoding="utf-8") if out else LOG  # noqa: SIM115
    r = subprocess.run([sys.executable] + args, stdout=f, stderr=subprocess.STDOUT, env=ENV, check=False)
    if out:
        f.close()
    if r.returncode:
        say(f"FAILED {r.returncode}")
        sys.exit(1)


def last(pattern, path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            found = re.findall(pattern, f.read())
    except FileNotFoundError:
        found = []
    return found[-1] if found else default


def complete(path, pairs=300):
    """A gate file holds all its pairs (herogate appends one line a pair and resumes from a partial file)."""
    try:
        with open(path, encoding="utf-8") as f:
            return sum(1 for line in f if line.strip()) >= pairs
    except FileNotFoundError:
        return False


def paired(a_path, b_path):
    """Mean over shared deals of A's X points minus B's X points, and its 95% half-width (as analysis/pilot/paired.py)."""
    def load(p):
        out = {}
        with open(p, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                xs = [g["points"] for g in r["games"] if g["arm"] == "x"]
                out[(r["k"], r["seed"])] = sum(xs) / len(xs)
        return out
    a, b = load(a_path), load(b_path)
    keys = sorted(set(a) & set(b))
    d = [a[k] - b[k] for k in keys]
    m = sum(d) / len(d)
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (len(d) - 1))
    return len(keys), 100 * m, 196 * sd / math.sqrt(len(d))


def eq_row(name):
    """A generation's equal-CPU N and gate file (the rerun when there was one)."""
    n2 = last(r"equal-CPU N (\d+)", f"{L}/{name}.log")
    if n2:
        return int(n2), f"{L}/gate-{name}-n{n2}.jsonl"
    return int(last(r"N (\d+) in-gate ratio", f"{L}/{name}.log", "100")), f"{L}/gate-{name}.jsonl"


gate = ["-m", "svsim.tools.herogate", "--hero", HERO, "--field", FIELD, "--base", "mcts:100+plan",
        "--opp", "mcts:100+plan", "--workers", str(W)]
G2, G3 = f"pilot-{DECK}-bot-g2", f"pilot-{DECK}-bot-g3"
N3, G3_ROW = eq_row(G3) if not DRY else (46, "g3.jsonl")
say(f"start prior {DECK}: hero {HERO}, g3 equal-CPU N {N3} ({G3_ROW}), deals {GATE3}, time {TIME}, workers {W}")

# 1. init
G2_ROW = f"{L}/gate3bank-g2-n{N3}.jsonl"
if not complete(G2_ROW):
    run(gate + ["--x", f"mcts:{N3}+plan+setnet={MODELS}/net-{G2}.npz+netmid+netany", "--seed", str(GATE3),
                "--pairs", "300", "--out", G2_ROW], out=f"{L}/gate3bank-g2-n{N3}.log")
if DRY:
    init, init_row = G3, G3_ROW
else:
    n, d, hw = paired(G3_ROW, G2_ROW)
    init, init_row = (G3, G3_ROW) if d >= 0 else (G2, G2_ROW)
    say(f"init: g3 - g2 on {n} deals = {d:+.1f} ± {hw:.1f} -> {init}")
NET = f"{MODELS}/net-{init}.npz"

# 2. decisions of gens 2 and 3
if not os.path.exists(f"{RUN}/dec.done"):
    os.makedirs(f"{RUN}/enc-dec", exist_ok=True)
    for f in glob.glob(f"{RUN}/rec-{SELF2}/rec-*.jsonl.gz") + glob.glob(f"{RUN}/rec-{SELF3}/rec-*.jsonl.gz"):
        dst = os.path.join(RUN, "enc-dec", os.path.basename(f))
        if not os.path.exists(dst):
            shutil.copy(f, dst)
    run(["analysis/pilot/setpolicy_named.py", "encode", "--records", f"{RUN}/enc-dec", "--out", f"{RUN}/dec",
         "--workers", str(W), "--deck", HERO])
    if not DRY:
        open(f"{RUN}/dec.done", "w").close()

# 3. fit
if not os.path.exists(PRI):
    shards = [str(b + 2 * i) for b in (SELF2, SELF3) for i in range(10)]
    run(["-m", "svsim.learn.setpolicy", "fit", "--data", f"{RUN}/dec", "--cards", f"{RUN}/tok/cards.npz",
         "--shards", *shards, "--init", NET, "--tau", "0.5", "--ftz", "--epochs", "35",
         "--checkpoint", f"{RUN}/ckpt-prior-{DECK}.npz", "--out", PRI], out=f"{L}/fit-prior-{DECK}-bot.log")

# 4. arm: time match, gate, equal-CPU rerun
X = f"+plan+setnet={NET}+netmid+netany+puct={PRI}:2:1"
tlog = f"{L}/time-prior-{DECK}-bot.log"
if not DRY and last(r"→ N 100 → (\d+)", tlog) is None:
    run(gate + ["--x", "mcts:100" + X, "--seed", str(TIME), "--time", "24", "--out", f"{L}/time-prior-{DECK}-bot.jsonl"],
        out=tlog)
N = int(last(r"→ N 100 → (\d+)", tlog)) if not DRY else 44
glog = f"{L}/gate-prior-{DECK}-bot.log"
run(gate + ["--x", f"mcts:{N}{X}", "--seed", str(GATE3), "--pairs", "300", "--out", f"{L}/gate-prior-{DECK}-bot.jsonl"],
    out=glog)
R = float(last(r"比 ([0-9.]+)", glog)) if not DRY else 1.2
say(f"N {N} in-gate ratio {R}")
row = f"{L}/gate-prior-{DECK}-bot.jsonl"
if R > 1.08:
    N2 = max(1, round(N / R))
    row = f"{L}/gate-prior-{DECK}-bot-n{N2}.jsonl"
    run(gate + ["--x", f"mcts:{N2}{X}", "--seed", str(GATE3), "--pairs", "300", "--out", row],
        out=f"{L}/gate-prior-{DECK}-bot-n{N2}.log")
    say(f"equal-CPU N {N2}")

# 5. the prior over its init net, both at equal CPU on the same deals
if not DRY:
    n, d, hw = paired(row, init_row)
    say(f"prior - {init} at equal CPU on {n} deals: {d:+.1f} ± {hw:.1f}")
say("done")
