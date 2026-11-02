# Process work (Salem 「开始」 2026-11-02 09:48Z, relayed by the architecture thread)

This branch takes items 2 and 5 of the process plan. The architecture thread takes items 1, 3 and 4; item 6 comes
later.

The plan file (/mnt/project-files/shadowverse/process-borrow-plan-2026-11-01.md) is not in this container. These
sections follow the architecture thread's spec message of 09:52Z.

Rules unchanged:
- Salem's games and the external lists never enter search, self-play or training; here they are checks only.
- The trainer (陪练台), ratings.json and installed models are not touched.

## Item 2: models bound to the simulator version (pre-registered before any code, 2026-11-02 ~10:05Z)

### What gets built

**One function, `rules_files()`, names the rules files:**
- `svsim/core/*.py`
- `svsim/cards/*.py`, except `deckcode.py`, `decks.py` and `demo.py`. Those are deck codes, deck lists and a demo;
  they are not game rules.
- `svsim/cards/data/*.json`, the card tables the engine loads.
- `__pycache__` is ignored.

**The rules hash.**
- RULES HASH = sha256 over those files, sorted by path, each fed in as its path and then its content.
- The model's info also keeps a short digest per file, so a mismatch can say how many files changed.

**At training time, the model's info gets a `provenance` record.** It holds the git commit, whether the rules files
were modified against it, the rules hash, the per-file digests, and the time. It is written by:
- `train_mid.py`, through `SetNet.save` at fit start.
- `setpolicy fit`.
- `SetNet.save` and `SetPolicy.save`, for any other trainer that writes one of these models without a record.

**At load** (`setnet.load_cached`, `setpolicy.load_cached`, which arena's `setnet=` and `puct=` use), the model is
compared with the current rules:
- A hash mismatch prints one warning line per model and process: the model, and how many rules files changed.
- A model with no record warns once as 「未登记」 and is not refused. Otherwise every existing net breaks.

**`herogate` and `deckgate` refuse a stale model by default.**
- This covers every `setnet=` and `puct=` path in their specs.
- `--allow-stale` lets one through, and the run's output prints that the flag was given.
- The league scripts live on claude/deck-search; they can call the same guard (one function).

**Backfill: `python -m svsim.learn.provenance backfill MODEL...`**
- It stamps a legacy model with the current hash only when `git log <training commit>..HEAD -- <rules files>` is
  empty and the rules files are clean in the working tree.
- The training commit comes from the model's info when it records one. Otherwise it is the commit that first added
  the model file, and the command prints which one it used.
- The record notes that it was backfilled and from which commit. The arrays are unchanged.
- It is not run on any model unless asked. It rewrites the file, so the model's sha256 changes.

**List: `python -m svsim.learn.provenance list [DIR]`** (default `analysis/scaling/models`).
- It prints each model's name, commit and status: current, stale or 未登记.
- For a stale model it also prints the rules files changed since its commit.

### Acceptance

- Change any one card script and every hashed model lists as stale. Revert it and all are current again. Run as a
  check on a temporary edit, then reverted; nothing is committed.
- Unit tests cover:
  - the hash function: it is stable, a one-byte change in a rules file changes it, and a non-rules file does not;
  - stamping on save;
  - the load warning, for stale and for 未登记;
  - the refuse path and the `--allow-stale` path of the gate guard;
  - the backfill's eligibility check.
- The existing suite still passes (exit code checked).

### Predictions (before any code)

- The plan's own: on launch day no model is flagged stale, 0.7. No existing model has a record, so on launch day
  they all list as 未登记, and stale can only come from models trained or backfilled after launch.
- Mine: of the 89 models now under `analysis/scaling/models`, at most 15 pass the backfill check (no rules-file
  change since the commit that added them), 0.7. The set-10 card scripts changed until late October.
- Mine: at least the Portal pair's models pass it (the 6 Portal nets and 2 priors, all trained after the last
  rules-file commit), 0.7.

### Item 2 results (written after the code)

- Code: `svsim/learn/provenance.py` (832c37e; the 「待复测」 label in 9d5a498). It hooks into:
  - `SetNet.save`, `WideSetNet.save` and `SetPolicy.save`: stamp if there is no record;
  - `train_mid.py` and `setpolicy fit`: stamp at training start;
  - `setnet.load_cached` and `setpolicy.load_cached`: warn;
  - `herogate` and `deckgate`: the guard and `--allow-stale`.
- `rules_files()`: 26 files today. Rules hash de145991df27d6a7….
- Acceptance check, on copies stamped in a scratch folder (no real model rewritten):
  - one line appended to `svsim/cards/portal.py` → both stamped models list as 待复测, with `portal.py` named, and
    herogate refuses the stale net;
  - the edit reverted (`git diff` empty) → both current again;
  - the legacy copy stays 未登记 throughout.
- Tests: `tests/test_provenance.py` 6 passed. Full suite: 1423 passed, 4 skipped, exit code 0.
- Predictions:
  - The plan's "on launch day no model is flagged": **TRUE**. All 86 models list as 未登记; none is 待复测.
  - Mine, "at most 15 of the models pass the backfill check" (0.7): **FALSE**.
    - 18 pass: the 6 Portal nets and 2 Portal priors, the 3 bot rune nets, and net-s1-10k, -20k, -a400, -b60 and -ii
      with prior-s1-20k and -60k.
    - The other 68 have 15 rules files changed since the commit that added them.
    - (Also: 86 of the 89 files in `analysis/scaling/models` are models; the other 3 are not .npz.)
  - Mine, "the Portal pair's models pass it" (0.7): **TRUE**, all 8.
- The backfill was only dry-run. It rewrites the model file (its sha256 changes), so it waits until someone asks.

## Item 5: one acceptance library (pre-registered before any code, 2026-11-02 ~10:20Z)

The plan's section 5, as the architecture thread quoted it at 09:56Z:
- One directory holds Salem's 4 replay points, the 11-01 bunny board, and every position from future replay reviews.
- One script runs any net and any prior over all of them and prints the pass rate.
- Each generation's gate report appends the pass rate.
- Two tiers: clear items and marginal items (margins of 0.04-0.08). Marginal pass rates are noisy and never gate
  alone.

### What gets built

**`analysis/acceptance/positions/<id>.json`, one file per position.** Each file holds:
- the side to judge, its deck, and the opponent's deck, as deck codes in the file;
- how to rebuild the position;
- the fingerprint: the side's hand ids, field ids, pp and leader hp;
- Salem's line and reason, in his words where they exist, and the line he calls wrong;
- the scorings that apply: turn-end, mid-turn, prior first step, hand-set evaluation;
- the tier: clear or marginal.

**Rebuilding is from the engine only.**
- A replay position stores the deal seed and which side goes first, and the full action list up to the position.
- The action list is recorded once, by replaying the old recipe (mcts:100+plan from the deal, as acceptance.py does)
  with the current engine. After that the rebuild applies the stored actions; no search runs. A change to search or
  evaluation no longer moves the position.
- A rebuild whose fingerprint differs from the stored one is an error: the item is not scored.
- The bunny board is built by hand (salem_board_2026_11_01.py sets the zones directly), so its file names that
  builder and stores its fingerprint.

**Scorings.** A line is a list of action descriptions applied in order.
- Turn-end: the net's turn-end score after the line and the end of the turn.
- Mid-turn: the net's mid-turn branch on the state right after the line.
- Hand-set evaluation: search.evaluate after the end of turn, as acceptance.py does.
- In each of these, an item passes when Salem's line scores above every wrong line. The score is the mean over 40
  reseeded copies, as acceptance.py does, so random effects average out.
- Prior: the prior's probability of the first step of Salem's line against the first step of the wrong line
  (prior_acceptance.py's rule; item 1's wrong line is ending the turn).
- The bunny board uses only the hand-set evaluation for now.

**One script: `analysis/acceptance/run.py [--net PATH] [--prior PATH] [--deck LABEL]`.**
- It prints each item, then the pass rate per scoring and per tier.
- `herogate` prints the same line at the end of a gate when the hero deck has positions and the X spec names a net or
  a prior.

**Inputs.**
- The deck lists come from claude/deck-search (dfm-2026-10-31.txt, league5/roster.txt). Only the lines needed go into
  the position files; no list file is copied.
- The models are net-pilot-rune-dfm-g3, prior-pilot-rune-dfm-ft-t05 and the round-2 prior. They are asked of the
  architecture thread; they are not on any branch yet.

### Acceptance (the plan's)

- The two existing scripts (acceptance.py and prior_acceptance.py) merge into one.
- The merged script reproduces the reported numbers:
  - 三轴土 g3: turn-end 2/4, mid-turn 3/4;
  - prior-pilot-rune-dfm-ft-t05 passes 锅 before 光 (0.405 vs 0.234);
  - the round-2 prior passes all four;
  - the hand-set evaluation fails the bunny board (keep 3.39 < all 3.72).
- The fingerprints of the four replay positions match prior_acceptance.py's printed fingerprints.
- Unit tests:
  - a stored position rebuilds to its fingerprint;
  - a changed fingerprint is reported, not scored;
  - the tier split is counted correctly.

### Tiers (fixed before any score is computed here)

An item is marginal when the reference value net's margin between Salem's line and the wrong line was under 0.10 on
the scale the plan uses. The plan's marginal items have margins of 0.04-0.08 under g2. Which items those are is asked
of the architecture thread, and they are written into the files before the script runs any net.

### Predictions (before any code)

- The four replay positions rebuild by the stored action lists to the same fingerprints the old recipe gives today:
  0.9.
- The merged script reproduces all four reported numbers within rounding: 0.7. A number that doesn't reproduce is
  reported as is, with the difference found.
