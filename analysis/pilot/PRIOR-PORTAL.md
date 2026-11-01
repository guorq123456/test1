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
- The fit is running: hero decisions of 86008000 and 86035000, 20 shards.
