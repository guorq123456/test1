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
