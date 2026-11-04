# Mirror self-play for the pilot nets (the architecture thread 2026-11-01 03:1xZ, before any mirror game)

Condition: 对手卡表已知（牌序、手牌未知）.

## What happened first (g1, the field recipe)

| hero | self-play hero score | g1 gate (time-matched, 300 pairs) |
|---|---|---|
| bot/T3-RUNE-1 | 25.9% | 18.2% vs 25.5%, **-7.3 ± 3.8** (at N 100 untimed: -8.3 ± 3.7) |
| dfm/RUNE-ユーリ (EXTERNAL) | **5.8%** (holdout 5.6%) | 7.8% vs 6.5%, **+1.3 ± 2.9** (N 58, bank 85997000) |

Salem's four positions (analysis/resource-value/acceptance.py on claude/deck-search) with net-pilot-rune-dfm-g1: 1/4
(the 物证 one only), and the two lines differ by 0.04-0.26 logit at logits of -3 to -5.

## Why (inferred, 0.7)

A value net trained on game results learns the win chance **under the pilot's own later play**. The untrained pilot
wins 5.8% with 三轴土 and does not turn earth sigils or spellboost into damage later, so under that pilot four sigils
now are worth almost nothing, and the net learns exactly that. Generations can only break this if each one already
plays a little better; at a 6% floor the labels are nearly all losses. The precedent nets were trained on MIRRORS
(ramp-t, elf-t: analysis/scaling/README.md), where results are 50/50 and the side that converts its resources better
wins: that is the signal we want.

## The arm

- Field `fields/dfm-yuri-mirror.txt`: the DFM list against itself (a second label, same code). Hero seat g % 2.
- Self-play: mcts:100+plan both sides, 10 shards x 1000, base 86015000 stride 2.
- Two nets, train_mid --shared --fresh, the builder's settings:
  - M: mirror shards only -> net-pilot-rune-dfm-m1;
  - MF: mirror + the g1 field shards (85995000:10) -> net-pilot-rune-dfm-mf1.
- Gate each in the field exactly as g1: herogate, field dfm-yuri-vs-bot6.txt, bank 85997000 (the same deals as g1's
  gate, so the baseline games repeat), 300 pairs, N time-matched once on 85997900.
- Acceptance: Salem's four positions with each net.
- The bot's own rune gets the same mirror arm on the builder's machine after its gen 2 (self-play base 86010000, gate
  on its g1 bank 85992000).

## Predictions (before any mirror game)

- M or MF beats the baseline (interval above 0): 0.3.
- M or MF passes at least 2 of Salem's 4 positions: 0.35.
- MF's paired difference is above g1's (+1.3): 0.6.

Isolation as for g1: net-pilot-rune-dfm-* models stay out of git, out of any deck search, 陪练台 and the web models.

## Paused (03:3xZ, after 1000 mirror games)

The bot rune hero's gen 2 (the builder, c1fdb2d) beat its baseline: +8.3 ± 4.3 (34.2% vs 25.8%, X with 19% more CPU;
an equal-CPU check is ordered). So one generation of the net playing its own positions fixed what g1 got wrong, as in
the precedent, and my reading above ("a pilot this weak cannot teach the net") is overturned for the bot's deck.
Mirror games of 三轴土 cost 5.1 CPU s each (2.6x a field game). The mirror arm is paused (shard 86015000 complete,
two part files, resumable); DFM gen 2 runs first (hero mcts:58 + g1, self-play 85998000, gate 85999000), as the bot's
did. The mirror predictions above stay registered for whenever the arm resumes.
