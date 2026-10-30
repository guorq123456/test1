# Non-linear turn-end evaluator: pre-gate reading (cand-nl-ramp-ramp; not installed)

**Condition:** 对手卡表已知（牌序、手牌未知）.

**Task** (the architecture thread 2026-10-10 13:21Z): J51 and J60 point at the same thing. The linear evaluator
gives face damage one fixed price, so it can't tell a race from a fight over resources. Try a model whose prices can
change with the position. The search code is unchanged: `learn.model.LinearValue` already reads a hidden layer.

## The model (`nl_fit.py`)

- **Form:** E(x) = w · x + w2 · tanh(x W1 + b1), with x = (raw − mean) / std.
  - 16 hidden units.
  - The stock columns and the bias column don't feed the hidden layer.
  - The linear part keeps the version-2 signs; the hidden part is free.
- **Data, features and objective:** cand-kc-ramp-ramp's. The same examples, weights and calibration rows; version
  2 plus the kclock columns; cand-tl's contrast loss with μ 0.03 and L2 1e-4 (on all weights but the intercept).
- **Start:** exactly cand-kc. The linear part takes its coefficients and standardization; W1 ~ N(0, 0.1²), b1 = 0,
  w2 = 0.
- **Training:** full-batch Adam, lr 0.01, 1500 iterations, 463 s.
- No card ids, deck ids or pairing as inputs, and no per-card table.
- Every setting was fixed before any held-out read. The fit reproduces cand-kc's training read at its start
  (0.008476 / 74.95%).

**Files:** svsim/learn/phased_models/cand-nl-ramp-ramp/.

| file | sha256 |
|---|---|
| ramp-ramp-ended.json | 2e151816768efea6463e5591a5e04e9fe1033c2833be2534f73fef26c951f655 |
| ramp-ramp-act.json (the installed ACT) | f6638159…31cd0c2 |

**Agent string:** `mcts:N+plan+learned+phased=cand-nl-ramp-ramp`.

## 1. Held out (`nl_read.py`, data/read.json)

The held-out set is the labels' split "val": 1,992 labels, 39,219 examples, 937 starts, never used in fitting.
Intervals: 2000 resamples of starts.

| | contrast MSE (weighted) | sign agreement (weighted) |
|---|---|---|
| cand-kc | 0.011104 | 73.88% |
| **cand-nl** | **0.010274** | **74.37%** |
| cand-nl − cand-kc | **−0.00083 (−0.00156 to −0.00017)** | +0.49 points (−1.1 to +2.1) |

- On the training set: 0.006841 / 76.36%, against cand-kc's 0.008476 / 74.95%.
- Calibration log loss: 0.5908 (cand-kc 0.5959).
- **J62** (sign agreement at least 1 point higher than cand-kc's): **wrong**. It is +0.49, and the interval holds both
  0 and 1. The contrast loss drops clearly: −7.5%, with an interval clear of 0.

## 2. 329 and 455 (Salem's turn end against the bot's)

**At the turn end itself** (`analysis/lethal-clock/kc_ends.py`, data/ends.txt):

| | installed | cand-kc | cand-nl |
|---|---|---|---|
| 329: Salem / bot | 0.651 / 0.690 | 0.631 / 0.636 | **0.740 / 0.746** |
| 455: Salem / bot (step 0) | 0.272 / 0.324 | 0.295 / 0.339 | **0.343 / 0.345** |

- Both are still wrong, but the gaps shrink to 0.006 and 0.002.
- In 455, Salem's end beats 5 of the 24 runs' ends under cand-nl. Under the others it beats none.
- Puzzles 2 and 3 stay right: 0.577 / 0.423 and 0.510 / 0.315.

**After the opponent's reply** (`analysis/puzzles3/reply_ends.py`, data/reply_ends.txt; 16 determinizations, paired):
- The positions are the same as in J60. Each model scores them with its own turn-end (ENDED) model, at the
  opponent's turn end, from the opponent's side.
- The ACT reading J60 used is the same for every candidate, since they replace only the ENDED model.

| | reply | installed ENDED | cand-kc | **cand-nl** |
|---|---|---|---|---|
| 329 Salem − bot | greedy | −0.048 ± 0.038 | −0.005 ± 0.020 | **+0.011 ± 0.021** |
| 329 Salem − bot | mcts:1043 | −0.033 ± 0.006 | +0.008 ± 0.008 | **+0.025 ± 0.010** |
| 455 Salem − bot | greedy | −0.025 ± 0.034 | −0.051 ± 0.028 | −0.029 ± 0.040 |
| 455 Salem − bot | mcts:1043 | −0.005 ± 0.027 | −0.035 ± 0.022 | −0.013 ± 0.028 |

- **J61** (at least one of 329 / 455, under at least one reading, Salem's end first): **right**. In 329, after the
  reply, under both replies; with the mcts:1043 reply the interval is clear of 0.
- **Caveats:**
  - cand-kc also puts Salem first in 329 after an mcts:1043 reply, by a margin that barely clears 0.
  - The installed ENDED model doesn't.
  - 455 stays wrong under every model and reading.

## 3. Cost (`nl_cost.py`, data/cost.json)

`search.evaluate.evaluate` on 718 ENDED positions, five interleaved rounds, median.

| | µs per evaluation | 1043's iterations per second if only the evaluation changes |
|---|---|---|
| installed | 81.3 | 2137 (bench.py) |
| cand-kc | 108.9 | 2018 (−5.6%) |
| cand-nl | 205.4 | 1689 (**−21.0%**) |

- The hidden layer adds about 96 µs. Most of that is the numpy call overhead in `LinearValue.logit`: turning the
  feature list into an array, and three small array operations, for a 67 × 16 layer.
- It could be cut (for example, by standardizing into an array once), but that is a code change. The installed
  models have no hidden layer, so it wouldn't touch them.

## Summary for the gate

- **J61 right**, **J62 wrong**.
- The contrast loss drops 7.5%, with an interval clear of 0.
- At the turn end, 329 and 455 are nearly level (gaps 0.006 and 0.002); after a reply, 329 turns right.
- It costs about 21% of the iterations at equal wall clock as it stands.

## 4. The hidden layer made cheaper (the architecture thread 13:36Z; `learn.model.LinearValue._hidden_out`)

**The change** (model.py only; the search code is unchanged):
- A small hidden layer is now summed in plain Python. "Small" means at most 4096 weights that can be nonzero:
  cand-nl's 16 units over 71 inputs, skipping W1's all-zero rows.
- A larger layer keeps the old numpy code. The linear part is the old Python sum for every model.

**Why Python and not numpy:** numpy in the search's hot path costs more than the layer itself.
- As a test, I added a dummy numpy layer of cand-nl's size to the installed model's evaluation, leaving the value
  unchanged. The evaluation took about 44 µs longer per iteration, and the rest of the search took 55–110 µs longer.
- In the search, with cand-nl: numpy written as one pass ran 1498–1530 iterations a second; plain Python 1751–1766.

**Checks** (data/logit_check.json, pz_old.txt / pz_new.txt):
- Installed and cand-kc: logits bit-identical on the 718 turn ends. Golden record identical; cmp_roots
  142cc567…2b9adf.
- The two old MLP candidates (cand-mlp-e2 / x1, 64 units: the numpy path) stay bit-identical.
- cand-nl: largest |old − new| logit 1.1e-15 (the hidden sums run in another order).
- Puzzle bank, seeds 1–8 (7 puzzles, 56 runs): every end the same, old code against new (4/40 solved either way).
- Full suite with the step-1 data: 1161 passed, 1 skipped.

**Speed** (nl_speed.py: ISMCTS.choose on 28 step-1 starts, 4 alternating rounds, median; data/speed_py.json):

| | iterations per second | vs installed |
|---|---|---|
| installed | 2145 | — |
| cand-kc | 2040 | −4.9% |
| cand-nl, plain Python (now) | **1766** | **−17.7%** |
| cand-nl, numpy (before) | 1498 | −29.3% |

- Per evaluation (nl_cost.py, data/cost_py.json): 205.4 → 166.8 µs for cand-nl. Installed: 86 µs, cand-kc: 100 µs.
- The iteration count is fixed, so the rate carries over to mcts:1043 (the same evaluation per iteration). At equal
  wall clock, cand-nl gets about 82% of the installed search's iterations.
