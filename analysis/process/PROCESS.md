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

## Item 5: one acceptance library

(pre-registered before its code; to follow)
