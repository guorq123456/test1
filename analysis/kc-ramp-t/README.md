# cand-kc-ramp-t: the lethal-clock turn-end model for the tournament Ramp (ramp-t) mirror, and pkg-kc-ramp2

**Condition:** 对手卡表已知（牌序、手牌未知）.

**Task:** the architecture thread 2026-10-13 23:58Z.
- pkg-kc-ramp-ramp changed only the original (Game8) Ramp mirror's turn-end model. The ramp-t mirror read the
  installed model, so the lethal clock did nothing there.
- This is cand-kc's recipe on the ramp-t mirror, plus a package that changes both mirrors.

## Data (cand-kc's way: the analysis line's step 1, rerun on ramp-t; bank 69900000, registered in its seed-banks.md)

- **Script:** step1_rampt.py, the analysis line's step1.py (f068d2b) with three changes: BANK 69900000, the
  ramp-t / v2s header command, and `gend --shard I/N`.
- **Self-play:** 1000 games, ramp-t vs ramp-t, v2s (= mcts:200+plan+learned+phased), explore 0, netdata seed
  69900000.
- **Starts:** 2000 of the 19,613 own-turn starts; 164 held out (g % 11 == 0).
- **Plans:** the build line's generator.
- **T:** 2 seeds × 8 determinizations per start, 4000 rows.
- **G_end:** K = 4 on training starts, 16 on held-out ones.
  - Odd k: the analysis line (79a9571).
  - Even k: this machine, plus chunks 09–17 by the analysis line (1113b16).
  - The runs were stopped by tool time limits and container restarts, and resumed by start. Seeds are derived from
    k, so the pieces are what one run gives.
  - krt_merge.py merged them: all 2000 starts, each once; every start's turn-end rows = K × its plans.
  - Determinism: starts that were run twice gave identical result rows (129 here and 84 on the analysis line), 0
    different.
- **Labels:** step1.py labels on this run's data (step-1 source only; the card-value teacher re-run exists only for
  the original mirror).
  - 5618 labels; 1340 pairs without contrast left out.
  - Calibration on 3997 training pairs without end: b = 0.371 (the original mirror's step 1: 0.888), per-game
    variance 0.282, τ² = 0.01696; end weight × 0.386.
- **Files:** data/ (sha256 of the merged G_end: gend.jsonl f563520b…94b6, gend_ends.jsonl.gz 1ea49767…ffae;
  labels.jsonl 11434a1c…d59e).

## Fit (krt_extract.py, krt_fit.py)

- **Features:** the installed ramp-t mirror model's (version 2 + "hand" + "hpphase", 87 columns, a6fdf0a's C3)
  plus "kclock" (7), 94 columns. No card ids; no fixed value per card.
- **Recipe:** cand-kc's (learn.contrast.fit_contrast):
  - μ 0.03, L2 1e-4, start at zero, 3000 iterations, lr 0.05;
  - the version-2 signs, the hand / hpphase / kclock columns free;
  - STOCK zeroed; intercept free (−0.2045).
- **Data used:** 100,864 training examples from 5053 labels; 16,918 calibration rows.
- **Output:** svsim/learn/phased_models/cand-kc-ramp-t.
  - ramp-t-ramp-t-ended.json is the fit; sha256 d63a5aaf…3a17.
  - ramp-t-ramp-t-act.json is the installed one; d6067af7…7d81.

## Readings against the installed ramp-t model (v2s)

**Contrast on the step-1 labels** (weighted, as cand-kc's reads):

| | training: error / same sign | held out (467 labels): error / same sign |
|---|---|---|
| installed ramp-t-ramp-t-ended | 0.015254 / 69.32% | 0.013250 / 68.61% |
| **cand-kc-ramp-t** | 0.004324 / 73.78% | **0.008986 / 69.58%** |

- Calibration log loss of cand-kc-ramp-t: 0.612 training, 0.6236 held out.

**step1.py holdout** (the held-out reading fixed before step 1's data): 164 held-out starts, 471 pairs; intervals
by resampling starts.

| | new | installed | new − installed |
|---|---|---|---|
| same sign as ΔG_end (K = 16), without end (290 pairs) | 68.6% | 70.0% | −1.4 (−6.2 to +3.6) |
| same sign as ΔT, without end (367 pairs) | 78.1% | 73.2% | **+4.9 (+0.5 to +9.3)** |
| same sign as ΔG_end, with end (384) | 75.8% | 76.8% | −1.0 (−4.6 to +2.7) |
| same sign as ΔT, with end (471) | 82.7% | 78.9% | +3.8 (+0.4 to +7.2) |

- The new model follows the teacher T better, clear of zero.
- Against the games played out (ΔG_end) it is level with the installed model: −1.4, interval across zero.
- For reference only: cand-kc's own held-out check on the original mirror (check_h.py, a different reading on
  other starts) gave ΔT same-sign +0.2 and ΔG_end +1.8 over the installed model there.

**Clock coefficients** (standardized), all small:
- me_kill_turns +0.021, op_kill_turns +0.011, kill_lead −0.011;
- op_hp_x_kill_lead +0.082, me_hp_x_kill_lead −0.045;
- op_hp_x_me_near +0.011, me_hp_x_op_near −0.022.

**Puzzles 2 and 3:** the bank's operations puzzles are original Ramp mirror positions; there is none in the ramp-t
mirror, so none is read.

## The package pkg-kc-ramp2 (analysis/install/make_pkg.py --replace)

- **What it holds:** every installed model file byte for byte (24 files), except:
  - `ramp-ramp-ended.json`, from cand-kc-ramp-ramp (95acaf1e…a125);
  - `ramp-t-ramp-t-ended.json`, from cand-kc-ramp-t (d63a5aaf…3a17).
- **Checks** (PACKAGE.json, tests/test_install_packages.py):
  - files are the installed ones but those two;
  - loaded, only (ramp, ramp, ended) and (ramp-t, ramp-t, ended) differ;
  - an agent naming the package reads both new models.
- **Agent string:** `mcts:200+plan+learned+phased=pkg-kc-ramp2+xprune=3:3:cost` (v2skx with the new package). The
  gate (J89) is the analysis line's.
- Nothing is installed; installing is Salem's call.
