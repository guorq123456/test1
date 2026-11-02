# DFM rune hero: a move prior on top of the g3 value net (the architecture thread 2026-11-01 12:2xZ, before any game)

Condition: 对手卡表已知（牌序、手牌未知）. EXTERNAL list, isolated, measurement only (Salem 「隔离训练」).

## Where the value-net generations stand (equal CPU, 300 pairs each)

| gen | bank | X | baseline | paired |
|---|---|---|---|---|
| g1 | 85997000 | 7.8 | 6.5 | +1.3 ± 2.9 (N 58, ratio 1.157) |
| g2 | 85999000 | 10.8 | 4.5 | +6.3 ± 2.8 |
| g3 | 86026000 | 25.2 | 7.3 | +17.8 ± 4.0 |
| g3 | 86028000 | 23.5 | 5.3 | +18.2 ± 3.9 |
| g4 | 86028000 | 20.5 | 5.3 | +15.2 ± 3.7; g4 − g3 on the same deals −3.0 ± 3.8 |

Gen 4 added nothing: the value net alone has levelled off near 24% against the bot's six other decks. Salem's four
positions: g3 passes 3 of 4 (mid-turn branch); 锅 before 光 still fails.

## The lever

The precedent's next step after the value net was a move prior with PUCT at every node (analysis/scaling/README.md
section B; installed as `+puct=prior-*-ft-t05.npz:2:1`). For 三轴土 the search spends 50-60 iterations on turns of
eight to ten ordered steps; a prior learned from the net-guided search's own visits lets those iterations go to the
orders that matter.

- Data: the hero's decisions (`setpolicy encode --deck dfm/RUNE-ユーリ`) in the g3 and g4 self-play records
  (86025000 and 86027000, 20 shards; both net-guided).
- Fit: `setpolicy fit --init net-pilot-rune-dfm-g3 --tau 0.5 --ftz` (trunk fine-tuned, the precedent's ft-t05) ->
  prior-pilot-rune-dfm-ft-t05.
- Arm: X = mcts:N+plan+setnet=net-pilot-rune-dfm-g3+netmid+netany+puct=prior-pilot-rune-dfm-ft-t05.npz:2:1, N
  time-matched once on 86028900 against mcts:100+plan, then an equal-CPU gate on 86028000 (the same deals as the g3
  and g4 rows above), so X can be paired with g3 directly.

## Predictions (before any game)

- The prior arm beats g3 on the same deals by at least +3 points: 0.4.
- It passes 锅 before 光 (Salem's position 2) with the prior's own ranking (prior P(锅) > P(光) at that position): 0.45.

The bot rune hero gets the same step only if this one gains (its gen 4 is running first).

## Results (written after the runs)

- Fit: 766580 hero decisions (20 shards, the g3 and g4 self-play); validation cross entropy 1.4639 (epoch 24) ->
  1.4634 (epoch 34). Deviation: the run hit the container's 2 h limit at epoch 33 with the step size down to 1/256 of
  the start and the gain under 1e-4 over eight epochs, so it was resumed from its checkpoint with `--epochs 35`
  instead of waiting for the patience stop (up to 60 epochs). Kept: epoch 34.
- Salem's positions, asked of the prior (analysis/pilot/prior_acceptance.py, logs/prior-acceptance.log; the same
  positions as acceptance.py, checked card for card against claude/deck-search's replay): the pre-registered item,
  锅 before 光: P(锅) 0.405 > P(光) 0.234 -> passes (prediction 0.45). Not scored, reported: 零嘴 for 4 土 0.599 vs end
  turn 0.269; 物证 0.227 vs 解谜旋律 0.192 (end turn 0.238 is the top move there); 琪可 into the knight 0.200 vs 迷人怪兽
  0.066.
- Time match on 86028900: X at N 100 costs 2.52x the baseline per searched decision -> N 40. Gate on 86028000 at
  N 40: X 32.3%, baseline 5.3%, +27.0 ± 4.1, in-gate CPU ratio 1.288 (over 1.08) -> equal-CPU run at N 31.
- EQUAL CPU (N 31, ratio 1.124; g3's row was N 50 at 1.110): X 31.2%, baseline 5.3%, +25.9. Paired with g3 on the
  same 300 deals (gate4bank-g3-n50): 31.2 vs 23.5, **+7.7 ± 4.1** -> the first prediction (prior beats g3 by at
  least +3, 0.4) came true. By opponent (prior / g3 / baseline): 龙族 72/57/13, 主教 50/40/10, 精灵 27/24/3,
  皇家护卫 14/8/4, 梦魇 14/6/0, 超越者 10/6/2. In rating (1 logit ≈ 236): baseline -> prior ≈ +490, g3 -> prior ≈ +90.
- Both predictions came true. Next per the plan above: the bot rune hero gets the same step after its gen 4.

## Bot rune hero: the same step (written 15:1xZ, before its gen-4 gate and before any prior game)

The DFM arm gained, so bot/T3-RUNE-1 gets the same step.
- Data: the hero's decisions in the bot's net-guided self-play of gens 3 and 4 (86020000 and 86022000, 20 shards).
- Init: the better of g3 and g4 on the same deals (g4 if its paired difference against g3 on bank 86023000 is at least
  0, else g3); fit as above (`--tau 0.5 --ftz`, patience stop or 35 epochs, whichever first) ->
  prior-pilot-rune-bot-ft-t05.
- Arm: that net + `puct=prior-pilot-rune-bot-ft-t05.npz:2:1`; N time-matched on 86024900, gate on 86023000 (g4's
  gate deals); equal-CPU rerun at round(N / in-gate ratio) when the ratio is over 1.08; paired with the chosen net's
  own equal-CPU row on 86023000.
- Predictions: the prior arm beats its value net alone on the same deals by at least +3 points: 0.45 (the DFM arm
  did, +7.7; the bot list has fewer long ordered turns, so a smaller gain is likely). Its gain is smaller than the
  DFM arm's +7.7: 0.7.
- Bot gen 4 (16:3xZ): self-play hero 36.7% (g3 32.5%). Gate on 86023000 at its time-matched N 65 (in-gate ratio
  1.263): 39.3 vs 27.2, +12.2 ± 4.7. Same deals, the same N 58 as g3 (same net size, so the same CPU per iteration):
  g4 39.0 vs g3 36.5, **+2.5 ± 4.3** -> g4 adds little, as DFM's g4 (−3.0 ± 3.8): both rune pilots level off at gen
  3-4. By the rule above (paired difference at least 0) the prior starts from g4. A prior from g3 was also fitted
  while g4 trained (compute only, prior-pilot-rune-bot-g3init-ft-t05); it is not the registered arm.
- Exploratory, not registered (written before its games): the g3-init prior, fitted anyway, uses the idle cores
  while the g4-init prior fits: g3 + its prior, time-matched on 86024800, gate on 86023000, paired with g3 at N 58.
  It answers only "does a prior help the bot rune g3 net too"; the registered result is the g4-init arm.
- Exploratory result (17:1xZ): time match 2.228 -> N 45; gate N 45: 53.0 vs 27.2 (ratio 1.504); rerun N 30: X 50.7%,
  baseline 27.2%, +23.5 ± 4.6, ratio 1.232 (g3's N 58 row on these deals: 1.181, so about 4% more CPU than g3).
  Paired with g3 N 58: 50.7 vs 36.5, +14.2 ± 4.3. The cost per decision has a fixed part (N 45: 57 ms, N 30: 46 ms),
  so dividing N by the ratio does not reach 1.0. Not registered; it says the second bot prediction (gain smaller than
  the DFM arm's) will likely fail.
- REGISTERED bot arm (18:3xZ): g4 + prior-pilot-rune-bot-ft-t05 (g4 init, 33 epochs). Time match 2.248 -> N 44; gate
  N 44: 53.0 vs 27.2 (ratio 1.454); equal-CPU rerun N 30: X 53.8%, baseline 27.2%, +26.6, ratio 1.186 (g4's N 58 row
  on these deals: 1.160). Paired with g4 N 58: 53.8 vs 39.0, **+14.8 ± 4.6**; with g3 N 58: +17.3 ± 4.3.
  By opponent (prior / baseline): 龙族 75/41, 主教 58/27, 精灵 59/33, 梦魇 51/28, 超越者 41/11, 皇家护卫 39/23.
  Predictions: beats its value net by at least +3 (0.45): TRUE. Gain smaller than the DFM arm's +7.7 (0.7): FALSE,
  it is about twice as large in points (in rating: bot +268 from untrained, DFM +490, since DFM starts near 0%).
- Where the two rune heroes stand with the same recipe (value net generations + prior, equal CPU, each on its own
  deals): bot/T3-RUNE-1 53.8%, dfm/RUNE-ユーリ 31.2% against the bot's six other decks. The gap was ~21 points
  untrained, ~9 at g3, now ~22. Neither pilot has converged; no deck-strength conclusion (Salem's rule: a pro list's
  prior is strong; this field is the bot's own decks, not the real meta).
