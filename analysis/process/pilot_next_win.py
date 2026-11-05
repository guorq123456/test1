"""Pilot generation g2, g3 or g4 for one of the four new-PC bot heroes (PC-PILOTS.md), as pilot-gen.sh, for Windows.

    py analysis/process/pilot_next_win.py DECK GEN WORKERS      e.g.  py analysis/process/pilot_next_win.py forest 2 6

DECK is forest, sword, dragon or abyss; GEN is 2, 3 or 4. Run from the repo root (with PYTHONPATH set to it); resumable.
Seeds, the layout of PRIOR-HAVEN.md inside the deck's bank: gN self-play base + 1000 + 2000 (N - 1), gate + 1000,
time match + 1900. The hero self-plays as mcts:<g(N-1)'s gate N> + net g(N-1); the net is trained fresh on gens 1..N
with g1's holdout. Everything lives in g1's run directory runs/pilot-DECK-bot-g1.
From g4 on: its own token folders (tok4, mid4), so a prior fitting from tok/ meanwhile is untouched; and after the
gate, the previous generation's net on this generation's deals at its equal-CPU N, paired with it.
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
DECK, GEN, W = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
DRY = len(sys.argv) > 4
assert DECK in HEROES and GEN in (2, 3, 4), "DECK forest|sword|dragon|abyss, GEN 2|3|4"
if os.name == "nt":
    import ctypes
    k = ctypes.windll.kernel32
    k.SetPriorityClass(k.GetCurrentProcess(), 0x4000)   # below normal; children inherit
HERO, BANK = HEROES[DECK]
FIELD = "analysis/pilot/fields/bot-frozen7.txt"
RUN = f"runs/pilot-{DECK}-bot-g1"
NAME = f"pilot-{DECK}-bot-g{GEN}"
PREV = f"pilot-{DECK}-bot-g{GEN - 1}"


def self_base(g):
    return BANK if g == 1 else BANK + 1000 + 2000 * (g - 1)


SELF = self_base(GEN)
GATE, TIME = SELF + 1000, SELF + 1900
TRAIN = [self_base(g) for g in range(1, GEN + 1)]
TOK, MID = (f"{RUN}/tok", f"{RUN}/mid") if GEN < 4 else (f"{RUN}/tok{GEN}", f"{RUN}/mid{GEN}")
ENV = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONUTF8="1")
LOG = open(f"{RUN}/logs/{NAME}.log", "a", encoding="utf-8")  # noqa: SIM115


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


prev_n = int(last(r"N (\d+) in-gate ratio", f"{RUN}/logs/{PREV}.log")) if not DRY else 55
PREV_NET = f"analysis/scaling/models/net-{PREV}.npz"
assert DRY or os.path.exists(PREV_NET), PREV_NET
HSPEC = f"mcts:{prev_n}+plan+setnet={PREV_NET}+netmid+netany"
say(f"start {NAME}: hero {HERO} self {SELF} hero-spec {HSPEC} train {TRAIN} gate {GATE} time {TIME} workers {W}")

out = f"{RUN}/rec-{SELF}"
if len(glob.glob(f"{out}/rec-*.jsonl.gz")) < 10:
    run(["-m", "svsim.learn.scaledata", "play", "--pool", FIELD, "--hero", HERO, "--hero-spec", HSPEC,
         "--spec", "mcts:100+plan", "--base", str(SELF), "--stride", "2", "--shards", "0", "10", "--per-shard", "1000",
         "--workers", str(W), "--every", "500", "--out", out])
if not DRY and len(glob.glob(f"{out}/rec-*.jsonl.gz")) < 10:
    say("self-play incomplete")
    sys.exit(1)
for f in glob.glob(f"{RUN}/rec-*/rec-*.jsonl.gz") + glob.glob(f"{RUN}/holdout/rec-*.jsonl.gz"):
    dst = os.path.join(RUN, "enc", os.path.basename(f))
    if not os.path.exists(dst):
        shutil.copy(f, dst)
NET = f"analysis/scaling/models/net-{NAME}.npz"
if not os.path.exists(NET):
    run(["-m", "svsim.learn.scaledata", "encode", "--records", f"{RUN}/enc", "--out", TOK, "--workers", "4"])
    run(["-m", "svsim.learn.midrows", "encode", "--records", f"{RUN}/enc", "--out", MID, "--workers", "4"])
    holds = [re.search(r"rec-(\d+)\.jsonl\.gz", f).group(1) for f in glob.glob(f"{RUN}/holdout/rec-*.jsonl.gz")]
    ends = [x for b in TRAIN for x in ("--end", f"{b}:10")]
    mids = [x for b in TRAIN for x in ("--mid", f"{b}:10")]
    run(["analysis/scaling/train_mid.py", "--shared", "--fresh", "--tokens", TOK, *ends,
         "--mid-dir", MID, *mids, "--holdout", *holds, "--name", NAME,
         "--checkpoint", f"{RUN}/ckpt-{NAME}.npz"], out=f"{RUN}/logs/train-{NAME}.log")
X = f"+plan+setnet={NET}+netmid+netany"
gate = ["-m", "svsim.tools.herogate", "--hero", HERO, "--field", FIELD, "--base", "mcts:100+plan",
        "--opp", "mcts:100+plan", "--workers", str(W)]
tlog = f"{RUN}/logs/time-{NAME}.log"
if not DRY and last(r"→ N 100 → (\d+)", tlog) is None:
    run(gate + ["--x", "mcts:100" + X, "--seed", str(TIME), "--time", "24", "--out", f"{RUN}/logs/time-{NAME}.jsonl"],
        out=tlog)
N = int(last(r"→ N 100 → (\d+)", tlog)) if not DRY else 100
glog = f"{RUN}/logs/gate-{NAME}.log"
run(gate + ["--x", f"mcts:{N}{X}", "--seed", str(GATE), "--pairs", "300", "--out", f"{RUN}/logs/gate-{NAME}.jsonl"],
    out=glog)
R = float(last(r"比 ([0-9.]+)", glog)) if not DRY else 1.2
say(f"N {N} in-gate ratio {R}")
row, neq = f"{RUN}/logs/gate-{NAME}.jsonl", N
if R > 1.08:
    N2 = max(1, round(N / R))
    row, neq = f"{RUN}/logs/gate-{NAME}-n{N2}.jsonl", N2
    run(gate + ["--x", f"mcts:{N2}{X}", "--seed", str(GATE), "--pairs", "300",
                "--out", row], out=f"{RUN}/logs/gate-{NAME}-n{N2}.log")
    say(f"equal-CPU N {N2}")


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


if GEN >= 4:
    prow = f"{RUN}/logs/gate{GEN}bank-g{GEN - 1}-n{neq}.jsonl"
    if not complete(prow):
        run(gate + ["--x", f"mcts:{neq}+plan+setnet={PREV_NET}+netmid+netany", "--seed", str(GATE), "--pairs", "300",
                    "--out", prow], out=f"{RUN}/logs/gate{GEN}bank-g{GEN - 1}-n{neq}.log")
    if not DRY:
        n, d, hw = paired(row, prow)
        say(f"g{GEN} - g{GEN - 1} at equal CPU N {neq} on {n} deals: {d:+.1f} ± {hw:.1f}")
say("done")
