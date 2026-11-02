# Portal pair: a move prior on top of the value net (pre-registered 2026-11-01 ~21:45Z, before any prior game)

Condition: 对手卡表已知（牌序、手牌未知）. dfm/PORTAL-MingiGod is an EXTERNAL list (Salem 「隔离训练」): its models
(*-dfm-*) are measurement only, never in deck search, the trainer or web models, never installed.

The architecture thread asked for this step on 2026-11-01 18:35Z. It follows the rune heroes' recipe
(claude/pilot-dfm `analysis/pilot/PRIOR.md`, 602ae759). There, the move prior was the lever once the value-net
generations levelled off. At equal CPU, paired on the same deals:
- DFM rune: g3 + prior was +7.7 ± 4.1 over g3.
- Bot rune: g4 + prior was +14.8 ± 4.6 over g4.

## Recipe, per hero (run after that hero's gen 3 is gated)

1. **Init.** Start from the better of g2 and g3 on the same deals. The rule: take g3 if g3 − g2 ≥ 0.
   - Measure it by playing g2 on g3's gate bank at g3's equal-CPU N. The nets are the same size, so the CPU per
     iteration is the same.
   - Pair that against g3's own equal-CPU row (analysis/pilot/paired.py from claude/pilot-dfm).
2. **Data.** The hero's decisions in the net-guided self-play of gens 2 and 3 (20 shards).
   - Encoded with claude/pilot-dfm's `analysis/pilot/setpolicy_named.py encode --deck <hero>`. Pool records replay
     with an empty deck name, and this wrapper fills it in.
3. **Fit.** `python3 -m svsim.learn.setpolicy fit --init <net> --tau 0.5 --ftz --epochs 35`
   - Output: `prior-pilot-portal-<dfm|bot>-ft-t05.npz`.
4. **Arm.** X = `mcts:N+plan+setnet=<net>+netmid+netany+puct=<prior>:2:1`.
   - Time-match N once against mcts:100+plan, on a fresh seed.
   - Gate 300 pairs on that hero's gen-3 gate bank.
   - If the in-gate CPU ratio is over 1.08, rerun at equal CPU with round(N / ratio).
   - Pair it with the chosen net's own equal-CPU row on the same deals, and report both CPU ratios. The prior's
     cost has a fixed part, so the rerun lands near 1.2, not 1.0.

Seeds:

| hero | self-play (gens 2, 3) | gate bank | prior time match |
|---|---|---|---|
| dfm/PORTAL-MingiGod | 86008000, 86035000 | 86036000 | 86039800 |
| bot/T1-PORTAL-1 | 86003000, 86030000 | 86031000 | 86034800 |

## Predictions (before any prior game)

**DFM Portal** (g3 at equal CPU: +18.8 ± 4.7 over the baseline, X 53.8%):
- (D1) The prior arm beats its value net alone on the same deals by at least +3 points: 0.6. Both rune heroes
  gained; this list's net-guided pilot still scores only about 50% against the field.
- (D2) Its gain is larger than DFM rune's +7.7: 0.4.

**Bot Portal** (g2 at equal CPU: +5.0 ± 4.4, X 71.7%; gen 3 not yet run):
- (B1) The prior arm beats its value net alone on the same deals by at least +3 points: 0.5. The hero already scores
  about 70%, so it has less room.
- (B2) Its gain is smaller than the DFM Portal arm's gain: 0.6.

## Results (written after the runs)

**DFM Portal.**
- Init. g2 on g3's gate deals (bank 86036000) at N 50 (ratio 1.040): X 50.5%, baseline 35.0%. Paired with g3's own
  N 50 row on the same 300 deals: 53.8% vs 50.5%, so **g3 − g2 = +3.3 ± 4.8**. That is ≥ 0, so the prior starts from
  g3. Logs: `logs/portal-dfm/gate3bank-g2-n50.*`.
- Fit: 761499 hero decisions (20 shards: the g2 and g3 self-play, 86008000 and 86035000), init net-pilot-portal-dfm-g3,
  `--tau 0.5 --ftz`. Validation cross entropy 1.5440 (epoch 1) → 1.5255 (epoch 20; unchanged to 4 decimals through
  epoch 32). It stopped on patience at epoch 32 of 35 → `prior-pilot-portal-dfm-ft-t05.npz`, 78 min. Log
  `logs/portal-dfm/prior-dfm.log`.
- Time match on 86039800: X at N 100 costs 2.020x the baseline per searched decision → N 50.
- Gate on 86036000 at N 50: X 61.3%, baseline 35.0%, +26.3 ± 4.6; in-gate ratio 1.365 (over 1.08) → equal-CPU rerun
  at N 37.
- **Equal CPU (N 37, ratio 1.174)**: X 62.5% ± 4.2%, baseline 35.0%, **+27.5 ± 4.7** over the baseline.
  - By opponent (prior / baseline): Dragon 84/41, Rune 84/56, Forest 67/43, Haven 56/30, Sword 45/19, Abyss 39/21.
  - Paired with g3's N 50 row on the same 300 deals: 62.5 vs 53.8, **+8.7 ± 4.5**.
  - CPU: g3's row ran at ratio 1.067, the prior arm at 1.174, so the prior arm used about 10% more CPU per searched
    decision than g3 did. The cost has a fixed part, so dividing N by the ratio does not reach 1.0 (the rune arms
    showed the same).
- Predictions:
  - (D1) beats its net by at least +3 (0.6): **TRUE**.
  - (D2) gain larger than DFM rune's +7.7 (0.4): **TRUE, narrowly**. +8.7 against +7.7 is well inside the noise.
- The route so far for this hero (equal CPU, paired over the baseline): g1 −7.2, g2 +10.3, g3 +18.8, g3 + prior
  +27.5. The X score went 27.2% → 62.5% against the bot's six other decks.

**Bot Portal.**
- Init. g2 on g3's gate deals (bank 86031000) at N 66 (ratio 1.062): X 75.8%, baseline 69.7%. Paired with g3's own
  N 66 row on the same 300 deals: 75.8% vs 75.8%, so **g3 − g2 = +0.0 ± 4.1**. That is ≥ 0, so the prior starts from
  g3. The value-net generations have levelled off for this hero (as the rune heroes did at gen 3-4). Logs:
  `logs/portal-bot/gate3bank-g2-n66.*`.
- Fit: 574635 hero decisions (20 shards: the g2 and g3 self-play, 86003000 and 86030000), init net-pilot-portal-bot-g3,
  `--tau 0.5 --ftz`. Validation cross entropy 1.4901 (epoch 1) → 1.4580 (epoch 29). It stopped on patience at epoch 33
  → `prior-pilot-portal-bot-ft-t05.npz`, 59 min. Log `logs/portal-bot/prior-bot.log`.
- Time match on 86034800: X at N 100 costs 1.633x the baseline per searched decision → N 61.
- Gate on 86031000 at N 61: X 82.0%, baseline 69.7%, +12.3 ± 4.1; in-gate ratio 1.310 → equal-CPU rerun at N 47.
- **Equal CPU (N 47, ratio 1.164)**: X 82.3% ± 3.3%, baseline 69.7%, **+12.7 ± 4.0** over the baseline.
  - By opponent (prior / baseline): Rune 99/87, Dragon 98/83, Forest 90/72, Haven 75/67, Sword 67/46, Abyss 65/63.
  - Paired with g3's N 66 row on the same 300 deals: 82.3 vs 75.8, **+6.5 ± 3.8**.
  - CPU: g3's row ran at ratio 1.081, the prior arm at 1.164, about 8% more CPU per searched decision.
- Predictions:
  - (B1) beats its net by at least +3 (0.5): **TRUE**.
  - (B2) gain smaller than the DFM Portal arm's (+8.7) (0.6): **TRUE** (+6.5; the difference between the two gains is
    well inside the noise).
- The route for this hero (equal CPU, paired over the baseline): g1 −10.5, g2 +5.0, g3 +6.2, g3 + prior +12.7. The X
  score went 57.3% → 82.3%.

## Where the two Portal heroes stand (equal CPU, each on its own gen-3 deals, against the bot's six other decks)

| hero | baseline mcts:100+plan | g3 | g3 + prior |
|---|---|---|---|
| bot/T1-PORTAL-1 | 69.7% | 75.8% | **82.3%** |
| dfm/PORTAL-MingiGod (EXTERNAL) | 35.0% | 53.8% | **62.5%** |

- The gap between the two was ~35 points under the baseline pilot and ~20 points with the trained pilots.
- Neither pilot has converged, and this field is the bot's own decks, not the real meta, so there is no conclusion
  about deck strength (Salem's rule).

## Head to head (pre-registered 2026-11-02 ~03:45Z, before any game)

The architecture thread asked for this on 2026-11-02 03:36Z, as the same step it ran for rune. There, the trained DFM
三轴土 scored 30.3% ± 3.5 against the trained bot rune; its prediction "at least 45%" at 0.35 was false.

- Field: `fields/portal-h2h.txt`, the two Portal lines.
- Hero: dfm/PORTAL-MingiGod, X = its g3 + prior at its equal-CPU N:
  `mcts:37+plan+setnet=net-pilot-portal-dfm-g3+netmid+netany+puct=prior-pilot-portal-dfm-ft-t05.npz:2:1`.
- Baseline: mcts:100+plan piloting the DFM list.
- Opponent, in every game: the bot Portal g3 + prior arm at its equal-CPU N:
  `mcts:47+plan+setnet=net-pilot-portal-bot-g3+netmid+netany+puct=prior-pilot-portal-bot-ft-t05.npz:2:1`.
- 300 pairs, seed 86039500 (unused), 4 workers.
- Reported: X (the trained DFM list's win rate against the trained bot list), the first/second split, the baseline row,
  and the CPU ratio.

Predictions:
- (H1) X is at least 45%: 0.25. Against the bot's six other decks the trained bot Portal scored 82.3% and the trained
  DFM Portal 62.5%, and the rune analogue came out at 30.3%.
- (H2) X beats the baseline row (mcts:100+plan on the DFM list against the same trained bot opponent) by at least
  +10: 0.6. The DFM prior arm was +27.5 over the baseline against the field.
