# Step 1 extras: the clock feature set and the contrast network (fit only, no gate)

The architecture thread 2026-10-09 11:12Z. Both are fitted on the same teacher pairs as the linear trial
(analysis/contrast-trial, ddfef2f): the analysis line's teacher_ends.jsonl.gz (753d531), pairs with a game over
during the turn left out (243,281 pairs over 384,337 turn ends), games with `g % 11 == 0` held out (22,491 pairs,
20,102 with dT != 0, 91 games; 1,583 calibration rows from the self-play turn ends). Settings as chosen there:
mu 0.03, L2 1e-4, start zero, 3000 iterations, the version-2 signs, the stock prefixes held at zero.

Condition: 对手卡表已知（牌序、手牌未知）.

- `c2_extract.py`: each pair's turn ends as version-2 + clock features and the network's set inputs (c2_data.npz,
  not committed).
- `c2_compare.py` (compare.log): linear+clock, then the network trained on top of it for 6 epochs, read after each
  epoch.
- `c2_ci.py` (ci.log): the read with its noise. It refits the linear version on the same file (clock columns held
  at zero), refits linear+clock, and trains the network for 6 epochs (fixed in advance) with seeds 0, 1 and 2. Each
  is compared with the linear version, with a 95% interval from resampling held-out games (2000 draws). The cost
  per evaluation is measured interleaved after a warm-up, as the median of 5 rounds over 57 turn ends.

The network (learn/contrast_net.py, 2,978 parameters) is the linear part plus a field set encoder for each side,
a DeepSets hand encoder (the hand-value student's), and one hidden layer of 32. The network part starts at zero,
so training starts from the linear+clock fit.

| held out | contrast MSE | sign | keep | noevo | save | calib log loss | µs / evaluation |
|---|---|---|---|---|---|---|---|
| linear (refit here) | 0.033685 | 72.52% | 72.10% | 75.83% | 68.19% | 0.5932 | 113 |
| linear + clock | 0.033643 | 72.49% | 72.24% | 75.54% | 67.08% | 0.5898 | 122 |
| network, seed 0 | 0.033658 | 72.80% | 72.53% | 75.64% | 68.26% | 0.5905 | 122 + 266 |
| network, seed 1 | 0.033575 | 72.78% | 72.49% | 75.59% | 68.47% | 0.5883 | |
| network, seed 2 | 0.033549 | 72.85% | 72.54% | 76.12% | 67.57% | 0.5878 | |

Difference from the linear version, 95% interval over held-out games:

| | MSE | sign | calib |
|---|---|---|---|
| linear + clock | [-0.00021, +0.00011] | [-0.54, +0.45] pt | [-0.0066, -0.0004] |
| network s0 | [-0.00035, +0.00029] | [-0.45, +0.97] pt | [-0.0073, +0.0016] |
| network s1 | [-0.00043, +0.00020] | [-0.38, +0.88] pt | [-0.0090, -0.0010] |
| network s2 | [-0.00043, +0.00016] | [-0.42, +1.05] pt | [-0.0101, -0.0009] |

For reference, ddfef2f's linear read on its own file: MSE 0.033694, sign 72.44%, calib 0.5933. Across epochs 1-6 of
seed 0 (compare.log) the network's MSE moves between 0.03349 and 0.03366 and its sign agreement between 72.6% and
73.3%, about as much as the gaps above.

Reading: neither is clearly better than the linear version. Every MSE and sign interval contains zero. Both
calibrate a little better (by about 0.003-0.005 log loss); that is the only difference whose interval excludes
zero. The clock adds about 9 µs. The network adds about 266 µs on top (encoding and a batch-of-one forward pass,
not optimized), so one evaluation costs about 3.4 times as much. With 91 held-out games, a gain over the linear
version larger than about 0.0004 MSE (1.3%) or about 1 point of sign agreement is ruled out on this data. Clock
coefficients (standardized): me_burst +0.20, op_burst -0.33, me_clock +0.03, op_clock +0.04, clock_lead +0.00.
