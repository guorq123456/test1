# Rune heroes, round 2 of the prior loop (written 18:4xZ 2026-11-01, before any of its games)

Condition: 对手卡表已知（牌序、手牌未知）. dfm/RUNE-ユーリ is an EXTERNAL list, isolated, measurement only.

Round 1 (PRIOR.md), equal CPU, against the bot's six other decks: DFM 三轴土 g3 + prior 31.2%; bot/T3-RUNE-1 g4 + prior
53.8%. Value-net generations alone had levelled off (g4 − g3: DFM −3.0, bot +2.5). The precedent (scaling README,
section B) went on by playing with the prior, then refitting both nets on the new games.

For each hero, the same steps:
1. Self-play 10 x 1000 with the round-1 arm as the hero (DFM: g3 + prior at N 31; bot: g4 + prior at N 30), the field
   at mcts:100+plan. DFM 86041000, bot 86043000 (stride 2).
2. Value net g5: fresh on all generations (DFM 85995000, 85998000, 86025000, 86027000, 86041000; bot 85990000,
   85993000, 86020000, 86022000, 86043000), holdout as before.
3. Prior 2: setpolicy fit on the hero's decisions in the newest two self-plays (DFM 86027000 + 86041000; bot 86022000 +
   86043000), init g5, tau 0.5, ftz, patience stop or 35 epochs.
4. Arm: g5 + prior 2, PUCT :2:1; time match (DFM 86044900, bot 86044800); gate on the round-1 deals (DFM 86028000,
   bot 86023000); equal-CPU rerun at round(N / in-gate ratio) when the ratio is over 1.08; paired with the round-1
   arm on the same deals.

Predictions:
- DFM round 2 beats DFM round 1 by at least +3 points: 0.5.
- Bot round 2 beats bot round 1 by at least +3 points: 0.4.
- The gap between the two (each on its own deals) narrows by at least 3 points: 0.45.
The DFM hero runs first (it is the measurement target); the bot hero after it, in the same container.

## Results

DFM (01:1xZ 2026-11-02):
- Self-play with the round-1 arm: hero 29.2% (round 1's own gate on other deals: 31.2%).
- g5: fresh on 50 shards, best epoch about 12 of 15 (valid log loss 0.3596). Prior 2: 35 epochs (one 2 h stop,
  resumed from its checkpoint), valid CE 1.3251.
- Time match 2.451 -> N 41; gate N 41: 33.3 vs 5.3 (ratio 1.347); equal-CPU rerun N 30: **34.7%**, ratio 1.129
  (round 1's N 31 row: 1.124). Paired with round 1 on the same deals: **+3.5 ± 3.8** (N 41: +2.2 ± 3.8).
- Prediction "at least +3" (0.5): the point estimate clears it, the interval does not exclude 0: a small gain at
  best. By opponent (round 2 / round 1): 龙族 73/72, 主教 47/50, 精灵 36/27, 梦魇 19/14, 超越者 17/10, 皇家护卫 16/14.

Bot (02:0xZ): self-play with the round-1 arm 49.8%; g5 fresh on 50 shards; prior 2 35 epochs (valid CE 1.4779).
Time match 2.583 -> N 39; gate N 39: 56.2 vs 27.2 (ratio 1.408); equal-CPU rerun N 28: **55.5%**, ratio 1.197 (round
1's N 30 row: 1.186). Paired with round 1: **+1.7 ± 3.8**.

Predictions: DFM at least +3 (0.5): +3.5 ± 3.8, met by the point estimate only. Bot at least +3 (0.4): FALSE. Gap
narrows by at least 3 (0.45): 22.6 -> 20.8, FALSE. The loop has levelled off for both at this budget: DFM ≈ 35%,
bot rune ≈ 55% against the bot's six other decks.

## Head to head (written 02:1xZ, before its games)

The field result mixes deck strength with matchups against the bot's own decks (the bot rune list was built against
this field). Direct test: the DFM round-2 arm (N 30) against the bot rune round-2 arm (N 28) as the opponent, field
= bot/T3-RUNE-1 only (fields/bot-rune-only.txt), 300 pairs on 86048000, both seats. The baseline arm (DFM at
mcts:100+plan) plays the same trained opponent.
Prediction: the trained DFM 三轴土 wins at least 45% of the head-to-head games: 0.35.
Result (02:2xZ): the trained DFM arm wins **30.3% ± 3.5** of 600 games against the trained bot rune arm (first 35.3%,
second 25.3%); DFM at mcts:100+plan wins 8.3% against it. Prediction (at least 45%, 0.35): FALSE. With pilots trained
the same way, the bot's own 巫师 beats DFM 三轴土 about 70-30 in this simulator. Per Salem's rule this indicts the pilot
or the simulator before the deck: the 三轴土 pilot levelled off at this budget, and the loss games are written out for
his review (analysis/pilot/watch_pilot.py; /mnt/project-files/shadowverse/watch-sanzhoutu-trained-2026-11-02.md).

## Budget test (written 04:0xZ, before its games)

The Portal pair gave the same picture (builder 58f317a: trained 人灭鱼 21.7% ± 3.3 against trained 造物鱼; untrained
16.0%). Both pro lists lose about 70-30 or worse to the bot's own lists when both pilots are trained the same way, at
the same small search budget (about 30 iterations a decision). If the pro lists need more search to show their
strength (longer ordered turns, more choices), the head-to-head should move toward them when both sides get more.
Test: the rune head-to-head again on the same 300 deals (86048000), both trained arms at four times their equal-CPU N
(DFM N 120, bot N 112), paired with the N 30/28 run.
Prediction: the trained DFM 三轴土 gains at least 5 points over its 30.3%: 0.35 (precedent: deeper play did not change
deck rankings with the hand-set evaluation; trained nets may differ).
