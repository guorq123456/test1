# Haven hero: a trained pilot for bot/T1-HAVEN-1 (pre-registered 2026-11-03 ~01:30Z, before any game)

Condition: 对手卡表已知（牌序、手牌未知）.

## Why

The architecture thread asked for this on 2026-11-03 01:21Z, citing F-18. In Salem's real game 6b, continued from
the same position, the bunny bishop bot (hand-set evaluation, no net) passed turn 1 seven times. Played on by the
same bot, passing there won 8.6 points less than playing a 1-cost card first. Haven is the weakest T1 craft, and
the only one whose pilot has not been trained yet.

Only the bot's own list is trained. DFM's 兔子教 (dfm/HAVEN-ユーリ) is not: among the external lists, only 三轴土
has Salem's isolated-training exception. Nothing is installed; this line only reports numbers.

## Recipe (the rune and Portal heroes' own, analysis/pilot/README.md, PRIOR.md, ROUND2.md, PRIOR-PORTAL.md)

- **Field.** `analysis/pilot/fields/bot-frozen7.txt`. Hero bot/T1-HAVEN-1 against the field's 6 other bot decks.
  The baseline and every opponent are mcts:100+plan, the hand-set bot without a net.
- **Generations.**
  - g1: 10 x 1000 self-play games with mcts:100+plan on both sides, plus a 2 x 1000 holdout.
  - gN (N ≥ 2): 10 x 1000 games with the hero piloted by mcts:<g(N-1)'s gate N> + net g(N-1). Then
    `train_mid --shared --fresh` on gens 1..N gives `net-pilot-haven-bot-gN`.
- **Each generation's gate.**
  - Time match once, 24 pairs: N = round(100 / ratio) unless the ratio is within 0.97-1.03.
  - Then 300 pairs against mcts:100+plan on the same deals.
  - Then an equal-CPU rerun at round(N / in-gate ratio) when that ratio is over 1.08.
- **Prior** (after g3 is gated).
  - Init: the better of g2 and g3 on the same deals; g3 if g3 − g2 ≥ 0.
  - Data: the hero's decisions in the gen-2 and gen-3 self-play (`setpolicy_named.py`).
  - Fit `--tau 0.5 --ftz --epochs 35`, which gives `prior-pilot-haven-bot-ft-t05`.
  - Arm: `+puct=<prior>:2:1`, time-matched, gated on g3's bank, with an equal-CPU rerun. It is paired with the chosen
    net's own equal-CPU row on the same deals.
- **Confirmation.** A conclusion stands only on the fixed confirmation bank (`herogate --bank confirm`): the gate
  banks, not the timing banks.
- **Seeds.** As allocated by the analysis session; none chosen here. They are written below when they arrive.

## Predictions (before any game)

- (H1) g3 at equal CPU beats the hand-set bot without a net (mcts:100+plan piloting the same list) by at least +5
  points, on g3's confirmation deals: 0.7 (the architecture thread's).
- (H2) g3 + prior at equal CPU beats g3 by at least +5 points more, on the same deals: 0.6 (the architecture
  thread's).
- (H3, mine) g1 is below the baseline (paired difference < 0): 0.7. Every hero's g1 so far lost: rune bot −7.3, DFM
  Portal −5.7, bot Portal −6.5.
- (H4, mine) The baseline (the hand-set bot) scores under 50% against the other six bot decks on g1's gate bank:
  0.75. Haven is the weakest T1 craft.

## Seeds

(waiting for the analysis session)

## Results (written after the runs)

(none yet)
