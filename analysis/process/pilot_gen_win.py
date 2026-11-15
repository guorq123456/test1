"""One pilot generation g1 for a bot hero, as migration/builder/scripts/pilot-gen.sh, for Windows.
Usage: py pilot_gen_win.py HERO NAME BASE WORKERS   (run from the repo root; resumable)"""
import glob, os, re, subprocess, sys, shutil, time
HERO, NAME, BASE, W = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
DRY = len(sys.argv) > 5
if os.name == "nt":
    import ctypes
    k = ctypes.windll.kernel32
    k.SetPriorityClass(k.GetCurrentProcess(), 0x4000)   # below normal; children inherit
FIELD = "analysis/pilot/fields/bot-frozen7.txt"
RUN = f"runs/{NAME}"
SELF, HOLD, GATE, TIME = BASE, BASE + 1000, BASE + 2000, BASE + 2900
ENV = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONUTF8="1")
os.makedirs(f"{RUN}/enc", exist_ok=True)
os.makedirs(f"{RUN}/logs", exist_ok=True)
LOG = open(f"{RUN}/logs/{NAME}.log", "a", encoding="utf-8")


def say(s):
    LOG.write(f"== {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {s}\n")
    LOG.flush()


def run(args, out=None):
    say(" ".join(args))
    if DRY:
        return
    f = open(out, "w", encoding="utf-8") if out else LOG
    r = subprocess.run([sys.executable] + args, stdout=f, stderr=subprocess.STDOUT, env=ENV)
    if out:
        f.close()
    if r.returncode:
        say(f"FAILED {r.returncode}")
        sys.exit(1)


def play(base, out, n):
    if len(glob.glob(f"{out}/rec-*.jsonl.gz")) >= n:
        return
    run(["-m", "svsim.learn.scaledata", "play", "--pool", FIELD, "--hero", HERO, "--spec", "mcts:100+plan",
         "--base", str(base), "--stride", "2", "--shards", "0", str(n), "--per-shard", "1000",
         "--workers", str(W), "--every", "500", "--out", out])


say(f"start {HERO} {NAME} base {BASE} workers {W}")
play(SELF, f"{RUN}/rec-{SELF}", 10)
play(HOLD, f"{RUN}/holdout", 2)
for f in glob.glob(f"{RUN}/rec-*/rec-*.jsonl.gz") + glob.glob(f"{RUN}/holdout/rec-*.jsonl.gz"):
    dst = os.path.join(RUN, "enc", os.path.basename(f))
    if not os.path.exists(dst):
        shutil.copy(f, dst)
NET = f"analysis/scaling/models/net-{NAME}.npz"
if not os.path.exists(NET):
    run(["-m", "svsim.learn.scaledata", "encode", "--records", f"{RUN}/enc", "--out", f"{RUN}/tok", "--workers", "4"])
    run(["-m", "svsim.learn.midrows", "encode", "--records", f"{RUN}/enc", "--out", f"{RUN}/mid", "--workers", "4"])
    holds = [re.search(r"rec-(\d+)\.jsonl\.gz", f).group(1) for f in glob.glob(f"{RUN}/holdout/rec-*.jsonl.gz")]
    run(["analysis/scaling/train_mid.py", "--shared", "--fresh", "--tokens", f"{RUN}/tok", "--end", f"{SELF}:10",
         "--mid-dir", f"{RUN}/mid", "--mid", f"{SELF}:10", "--holdout", *holds, "--name", NAME,
         "--checkpoint", f"{RUN}/ckpt-{NAME}.npz"], out=f"{RUN}/logs/train-{NAME}.log")
X = f"+plan+setnet={NET}+netmid+netany"
gate = ["-m", "svsim.tools.herogate", "--hero", HERO, "--field", FIELD, "--base", "mcts:100+plan",
        "--opp", "mcts:100+plan", "--workers", str(W)]
tlog = f"{RUN}/logs/time-{NAME}.log"
if not DRY and not os.path.exists(tlog):
    run(gate + ["--x", "mcts:100" + X, "--seed", str(TIME), "--time", "24", "--out", f"{RUN}/logs/time-{NAME}.jsonl"], out=tlog)
N = int(re.findall(r"→ N 100 → (\d+)", open(tlog, encoding="utf-8").read())[-1]) if not DRY else 100
glog = f"{RUN}/logs/gate-{NAME}.log"
run(gate + ["--x", f"mcts:{N}{X}", "--seed", str(GATE), "--pairs", "300", "--out", f"{RUN}/logs/gate-{NAME}.jsonl"], out=glog)
R = float(re.findall(r"比 ([0-9.]+)", open(glog, encoding="utf-8").read())[-1]) if not DRY else 1.2
say(f"N {N} in-gate ratio {R}")
if R > 1.08:
    N2 = max(1, round(N / R))
    run(gate + ["--x", f"mcts:{N2}{X}", "--seed", str(GATE), "--pairs", "300",
                "--out", f"{RUN}/logs/gate-{NAME}-n{N2}.jsonl"], out=f"{RUN}/logs/gate-{NAME}-n{N2}.log")
    say(f"equal-CPU N {N2}")
say("done")
