# MANIFEST-builder (the builder session's container, 2026-11-02 ~13:40Z)

Builder session: session_01MrDoGaowUWeii2Vq77vEnA. Repository: guorq123456/test1.

**Where this bundle is.** `/mnt/project-files` is not mounted in this container. It contains only attach, sandboxing,
skills and user-data, so the bundle could not be written to the migration inbox. It sits in this container's
scratchpad (`.../scratchpad/migration/builder/`), with a copy as `builder-bundle.tar.gz` next to it. See the end for
how it can reach the inbox.

Rules unchanged:
- Salem's games and every external list never enter search, self-play or training.
- The trainer (陪练台), ratings.json and main were not touched by this session.

## Branches

| branch | state |
|---|---|
| `ccr-165ad1e7-t2zmqu` (the only branch this session pushes) | head **63727a4**, fully pushed (0 commits ahead of origin) |

- The working tree is clean; nothing is uncommitted.
- Merged into it, unchanged:
  - claude/pilot-dfm up to 83fc182 (merge b4b2bb6);
  - claude/process a6572dc (merge 0185311).
- No other branch was created or pushed.

## What is in the repository already (no copy needed)

- **Models.** All models are committed under `analysis/scaling/models/`, 90 files. Since item 2:
  - `python -m svsim.learn.provenance list` shows 22 current and 68 未登记;
  - their data JSON is under `analysis/scaling/data/`.
- **Pilot line results.**
  - `analysis/pilot/README.md` and `PRIOR-PORTAL.md`.
  - Records and logs in `analysis/pilot/data/` and `analysis/pilot/logs/`: portal-bot, portal-dfm, portal-h2h, and the
    bot rune hero g1-g3.
- **Process items 2 and 5, and the rulings pins.**
  - `svsim/learn/provenance.py`;
  - `analysis/acceptance/`;
  - `analysis/process/PROCESS.md`;
  - `tests/test_provenance.py`, `tests/test_acceptance_lib.py`, `tests/test_rulings_pins.py`;
  - `docs/rulings.md`, with every entry pinned.

## Measurement-only models (never in deck search, never installed, never in the trainer)

All `*-dfm-*` (EXTERNAL lists, Salem 「隔离训练」):
- net-pilot-portal-dfm-g1, -g2, -g3
- prior-pilot-portal-dfm-ft-t05
- net-pilot-rune-dfm-g3, -g5
- prior-pilot-rune-dfm-ft-t05
- prior2-pilot-rune-dfm-ft-t05

The bot-deck pilot models (net-pilot-rune-bot-*, net-pilot-portal-bot-*, prior-pilot-portal-bot-ft-t05) are research
models too. None is installed; installing any model needs Salem's own words.

## What this bundle holds (not in the repository)

### `runs/`: the run folders minus the self-play data

Each run folder keeps its logs, gate and time-match `.jsonl`/`.log`, and training checkpoints (`ckpt-*.npz`, about
2.6-3.1 MB each). 245 files.

| folder | what | branch / commit of the results |
|---|---|---|
| `runs/pilot/` | bot/T3-RUNE-1 hero, g1-g3 (self-play, nets, gates, equal-CPU reruns) | ccr-165ad1e7-t2zmqu up to 392cd1c |
| `runs/pilot-portal-dfm/` | dfm/PORTAL-MingiGod hero (EXTERNAL), g1-g3 and the prior: generation logs, gates, time matches, `ckpt-*`, `logs/prior-dfm.log` | a7eeb0b, 888a4ad, 7097c53, c33eb76, 048c7b3, c71c2b1 |
| `runs/pilot-portal-bot/` | bot/T1-PORTAL-1 hero, g1-g3 and the prior | 1daf1f5, f0c9ad9, 479f1cd, 97993d1, 568fdc7 |
| `runs/s1/`, `runs/s1g/`, `runs/t1/` | shared-net line S1 and T1 (stopped): eval and training logs, checkpoints | analysis/sharednet (69e7577 and earlier) |
| `runs/checkup/` | bot-checkup deals (`c/deals.jsonl`, 5.3 MB) | merged from claude/bot-checkup |

### Not copied: self-play data

The rec, tok, mid, dec, enc and holdout folders are listed with byte sizes in `selfplay-dirs-not-copied.txt`, about
1.7 GB in all. The largest are `runs/s1/dec` 265 MB, `runs/s1/rec` 199 MB and `runs/s1/mid` 196 MB. The Portal and
rune pilot records the results rest on are in the repository anyway (`analysis/pilot/data/`). tok, mid and dec can
be rebuilt from them with `scaledata encode`, `midrows encode` and `setpolicy_named.py encode`.

### `scripts/`: the drivers from the scratchpad

156 `.sh`/`.py` files. The ones in use for the pilot line:
- `pilot-gen.sh`: one generation, in the stages `play`, `rest` or `all`, under one chunk deadline, `LIMIT` default
  6900 s.
- `prior-fit.sh`: encode the hero's decisions, then fit the prior.
- `prior-gate.sh`: time match, gate, equal-CPU rerun, then the pairing with paired.py.

The rest are drivers of earlier lines, kept for the record.

### `worktrees/`: the two scratch worktrees that were not clean

- `wt-j100` (HEAD 69e3ad2, the +neteot timing work): one modified file, `analysis/scaling/timing.py` (diff in
  `uncommitted.diff`).
  - Untracked: `analysis/scaling/data/timing-old.json`, and three models (net-elft-10000, net-gen3-30000,
    net-gen4-59000) that are byte-identical to the committed ones.
  - Old exploratory state; nothing open depends on it.
- `wt-r1` (HEAD fbb3c21): one untracked file, `relabel.py`, copied as is.
- The other ten scratch worktrees are detached at old commits and have no changes.

### Not copied, on purpose

- `data/raw/` (13 MB): official card data. Rule: it stays local and is never committed or moved; rebuild it with
  `python -m svsim.tools.build_pool` from local official data.
- `replays/` (2 small JSON files from 2026-10-06, `tools.play` saves): left where they are. If they hold Salem's
  games, they belong in /mnt/project-files only.

## Status

- **What I was doing.** Process items 2 and 5 are done and accepted, item 3's gate header lines are done, and the
  rulings pins (item 1's test list) are done and accepted (architecture thread 10:31Z).
  - The pilot line is paused waiting on Salem; the Portal pair's last result is the head-to-head, 58f317a.
  - Nothing is running; the machine is idle.
- **Next.** Item 6 waits for Salem's tracker data in /mnt/project-files/shadowverse/salem-games/tracker/. That data
  is for checks and showing Salem differences only, never training.
- **Known pitfalls.**
  1. **The 2-hour background task limit.**
     - Never put a whole generation in one task: self-play is about 2 h. Use `pilot-gen.sh ... play`, then `... rest`.
     - Each chunk gives every step what is left of one deadline. An outer `timeout` once killed the script but not
       its inner `timeout` child, which left orphaned workers writing the same part file.
     - A task killed at the 2-hour limit must not be restarted.
  2. **BLAS on one thread for every timing** (OMP/OPENBLAS/MKL_NUM_THREADS=1). Time matches and gates run only on an
     idle machine.
  3. **Equal CPU.** The prior's cost has a fixed part, so round(N / ratio) lands near 1.1-1.2, not 1.0. Report both
     ratios.
  4. **Pool self-play records replay with empty deck names.** Encode hero decisions with
     `analysis/pilot/setpolicy_named.py`.
  5. **Damage triggers are queued until the whole fanfare resolves.** An `on_damaged` probe can't see the order inside
     an ability.
  6. **4 cores only.** One fit (single process) can overlap self-play on 3 workers; timing cannot overlap anything.
  7. **The container restarted twice today.** Runs resume from `.part` files and checkpoints, and resuming after a
     restart is allowed.
  8. **`/mnt/project-files` is not mounted in this container**, which is why this bundle sits in the scratchpad.

## How this reaches the migration inbox (the architecture thread 13:34Z: option b)

Only this manifest, the 156 driver scripts, and the two worktrees' leftovers go into git. Those are wt-j100's
`timing.py` diff and `timing-old.json`, and wt-r1's one file, `relabel.py`. (An earlier draft put `relabel.py`
under wt-j100; it is wt-r1's.) Not pushed:
- run folders and checkpoints: every model is committed, and a checkpoint is only a resume state, so it can be
  retrained from the committed model;
- the tarball;
- `data/raw`: official card data never goes into the repository.

The full tarball stays in this container until it is reclaimed, then it is gone:
- path: `/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/migration/builder-bundle.tar.gz`
- size: 185656185 bytes
- sha256: `f68e6256093f799faa2ab23f089ad66e67ee404ceca2a431589e0f71b5ef9536`

`replays/`: not pushed. These are tools.play saves, so a person played one seat against
`mcts:200+plan+learned` (rhino vs ramp). The evidence says that person was Claude, in this same session's own five
Rhinoceroach games: 14aee57, 2026-10-06 04:39Z, docs/architecture.md「Claude 亲自操作破魔虫」, saved 18-30 minutes
earlier; Salem's games that evening are web saves. Salem can't be ruled out, so they were sent as raw text to the
architecture thread rather than committed:

| file | bytes | sha256 (first 16) |
|---|---|---|
| 20261006-042054-2026001.json | 5236 | c2fb60c8b547df96 |
| 20261006-042524-2026002.json | 4109 | a7b3d68714f9ea70 |
