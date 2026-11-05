"""The move prior for one of the four new-PC bot heroes (PC-PILOTS.md), as PRIOR-HAVEN.md, for Windows.

    py analysis/process/pilot_prior_win.py DECK WORKERS [A B]  e.g.  py analysis/process/pilot_prior_win.py forest 3

A B: the two generations it starts from, 2 3 (default) or 4 5; below, "g2/g3" stands for gA/gB. With 4 5 every file
name carries "-g5" (the prior, its logs, gates and checkpoint) and the time match is base + 11900; the init step
reuses gate5bank-g4-n<N>.jsonl when the g5 driver already played it.

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
DRY = "dry" in sys.argv[3:]
A, B = tuple(int(x) for x in sys.argv[3:] if x != "dry") or (2, 3)
TIMES = {(2, 3): 9800, (4, 5): 11900}       # time-match seeds inside the bank (the analysis ledger, ac6f25a1)
assert (A, B) in TIMES, "A B: 2 3 or 4 5"
SUF = "" if (A, B) == (2, 3) else f"-g{B}"
assert DECK in HEROES, "DECK forest|sword|dragon|abyss"
if os.name == "nt":
    import ctypes
    k = ctypes.windll.kernel32
    k.SetPriorityClass(k.GetCurrentProcess(), 0x4000)   # below normal; children inherit
HERO, BANK = HEROES[DECK]
FIELD = "analysis/pilot/fields/bot-frozen7.txt"
RUN = f"runs/pilot-{DECK}-bot-g1"
L = f"{RUN}/logs"


def self_base(g):
    return BANK if g == 1 else BANK + 1000 + 2000 * (g - 1)


SELFA, SELFB = self_base(A), self_base(B)
GATEB, TIME = SELFB + 1000, BANK + TIMES[(A, B)]
TOKB = f"{RUN}/tok" if B < 4 else f"{RUN}/tok{B}"
MODELS = "analysis/scaling/models"
PRI = f"{MODELS}/prior-pilot-{DECK}-bot{SUF}-ft-t05.npz"
ENV = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONUTF8="1")
LOG = open(f"{L}/prior-{DECK}-bot{SUF}.log", "a", encoding="utf-8")  # noqa: SIM115


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
GA, GB = f"pilot-{DECK}-bot-g{A}", f"pilot-{DECK}-bot-g{B}"
NB, GB_ROW = eq_row(GB) if not DRY else (46, "gB.jsonl")
say(f"start prior {DECK} from g{A}/g{B}: hero {HERO}, g{B} equal-CPU N {NB} ({GB_ROW}), deals {GATEB}, time {TIME}, "
    f"workers {W}")

# 1. init
GA_ROW = f"{L}/gate{B}bank-g{A}-n{NB}.jsonl"
if not complete(GA_ROW):
    run(gate + ["--x", f"mcts:{NB}+plan+setnet={MODELS}/net-{GA}.npz+netmid+netany", "--seed", str(GATEB),
                "--pairs", "300", "--out", GA_ROW], out=f"{L}/gate{B}bank-g{A}-n{NB}.log")
if DRY:
    init, init_row = GB, GB_ROW
else:
    n, d, hw = paired(GB_ROW, GA_ROW)
    init, init_row = (GB, GB_ROW) if d >= 0 else (GA, GA_ROW)
    say(f"init: g{B} - g{A} on {n} deals = {d:+.1f} ± {hw:.1f} -> {init}")
NET = f"{MODELS}/net-{init}.npz"

# 2. decisions of the two generations (one dec-<seed>.npz a shard; the fit picks its shards)
if not os.path.exists(f"{RUN}/dec{SUF}.done"):
    os.makedirs(f"{RUN}/enc-dec", exist_ok=True)
    for f in glob.glob(f"{RUN}/rec-{SELFA}/rec-*.jsonl.gz") + glob.glob(f"{RUN}/rec-{SELFB}/rec-*.jsonl.gz"):
        dst = os.path.join(RUN, "enc-dec", os.path.basename(f))
        if not os.path.exists(dst):
            shutil.copy(f, dst)
    run(["analysis/pilot/setpolicy_named.py", "encode", "--records", f"{RUN}/enc-dec", "--out", f"{RUN}/dec",
         "--workers", str(W), "--deck", HERO])
    if not DRY:
        open(f"{RUN}/dec{SUF}.done", "w").close()

# 3. fit (static rows added for cards seen only at decisions, such as the 梦魇 hero's Ghost token)
if not os.path.exists(PRI):
    cards = f"{RUN}/prior-cards{SUF}.npz"
    run(["analysis/process/extend_cards.py", f"{RUN}/dec", f"{TOKB}/cards.npz", cards])
    shards = [str(b + 2 * i) for b in (SELFA, SELFB) for i in range(10)]
    run(["-m", "svsim.learn.setpolicy", "fit", "--data", f"{RUN}/dec", "--cards", cards,
         "--shards", *shards, "--init", NET, "--tau", "0.5", "--ftz", "--epochs", "35",
         "--checkpoint", f"{RUN}/ckpt-prior-{DECK}{SUF}.npz", "--out", PRI], out=f"{L}/fit-prior-{DECK}-bot{SUF}.log")

# 4. arm: time match, gate, equal-CPU rerun
X = f"+plan+setnet={NET}+netmid+netany+puct={PRI}:2:1"
tlog = f"{L}/time-prior-{DECK}-bot{SUF}.log"
if not DRY and last(r"→ N 100 → (\d+)", tlog) is None:
    run(gate + ["--x", "mcts:100" + X, "--seed", str(TIME), "--time", "24", "--out", f"{L}/time-prior-{DECK}-bot{SUF}.jsonl"],
        out=tlog)
N = int(last(r"→ N 100 → (\d+)", tlog)) if not DRY else 44
glog = f"{L}/gate-prior-{DECK}-bot{SUF}.log"
run(gate + ["--x", f"mcts:{N}{X}", "--seed", str(GATEB), "--pairs", "300", "--out", f"{L}/gate-prior-{DECK}-bot{SUF}.jsonl"],
    out=glog)
R = float(last(r"比 ([0-9.]+)", glog)) if not DRY else 1.2
say(f"N {N} in-gate ratio {R}")
row = f"{L}/gate-prior-{DECK}-bot{SUF}.jsonl"
if R > 1.08:
    N2 = max(1, round(N / R))
    row = f"{L}/gate-prior-{DECK}-bot{SUF}-n{N2}.jsonl"
    run(gate + ["--x", f"mcts:{N2}{X}", "--seed", str(GATEB), "--pairs", "300", "--out", row],
        out=f"{L}/gate-prior-{DECK}-bot{SUF}-n{N2}.log")
    say(f"equal-CPU N {N2}")

# 5. the prior over its init net, both at equal CPU on the same deals
if not DRY:
    n, d, hw = paired(row, init_row)
    say(f"prior - {init} at equal CPU on {n} deals: {d:+.1f} ± {hw:.1f}")
say("done")
