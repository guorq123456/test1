# Where else can a rule prune? Wide decisions in the Ramp mirror, by kind (diagnostic, no gate)

**Condition:** 对手卡表已知（牌序、手牌未知）.

**Task:** the architecture thread 2026-10-10 18:37Z. Salem: 「算力不够可以用算法剪，不用硬搜」, discards being one
example. Find the next place a rule on visible information could prune like that.

## Data (`collect.py`; data/wide.jsonl, sha256 366f9531…f3e6)

- **Positions:** step 1's turn starts (RC 6f11111, Ramp mirror self-play), training split, starts 100–699.
- **Who plays:** the "strongest" tier (mcts:1043+plan+learned+phased, whole agent) plays each turn. At each of its
  decisions with **9 or more legal moves**, level-strong (mcts:200+plan+learned+phased, same seed) chooses on a
  copy.
- **"Different":** the two moves lead to different positions (state_key after each move).
- **Totals:** 348 wide decisions, mean 15.3 legal moves. The tiers choose differently at **33.9%** of them, the same
  rate as the earlier "34% different".

**Buckets by the kind of move the strongest tier chose** (kinds from the engine's actions; "discard" as in
search.xprune):

| bucket | share | strong ≠ strongest | mean legal moves |
|---|---|---|---|
| **play** (which card to play, no choice) | **38.5%** (134) | 29.9% | 13.6 |
| **discard** (a play / evolve whose hand targets are discarded) | **37.4%** (130) | **38.5%** | 17.9 |
| choose (a play with modes) | 9.2% (32) | 15.6% | 15.8 |
| attack the leader | 7.2% (25) | 40.0% | 14.5 |
| bonus play point | 3.2% (11) | 54.5% | 11.9 |
| attack a follower | 2.3% (8) | 37.5% | 10.9 |
| evolve / super-evolve | 2.0% (7) | 57% | 9.9 |
| end turn | 0.3% (1) | 0% | 9.0 |

**What makes them wide:**
- The legal moves at these decisions, by kind: discard choices 56.7%, plays 21.8%, end turn 6.6%, choose 3.9%,
  attacks 6.2%, evolves 3.9%, bonus 1.0%.
- In 79% of the wide decisions, the kind with the most legal moves is the discard choices.
- Where the tiers differ, the commonest pairs are:
  - discard vs another discard (30);
  - play vs discard (17 + 15 the other way round);
  - play vs another play (15).

## Rules tried on the two largest buckets (`rules.py`; data/rules.json)

**Retention:** the share of decisions where the strongest tier's move is still among the moves left (judged by
the position it leads to). **Cut:** the share of legal moves removed.

1. **Discard bucket, search.xprune** (as gated, `+xprune=3:3:cost`, and the first version m 2 when):

   | rule | retention in the bucket (130) | moves cut in the bucket | retention over all 348 | moves cut over all |
   |---|---|---|---|---|
   | xprune m 3 cost | 65.4% | 33.5% | 87.1% | 26.3% |
   | xprune m 2 when | 52.3% | 46.5% | 82.2% | 37.5% |

   - It never cuts a move in the play bucket: 100% retention there.
   - On these self-play positions the strongest tier's discards are cut more often than in analysis/xprune
     (27–40% there).

2. **Play bucket, "budget" rule** (new, analysis only):
   - B is the most play points any set of hand cards can use this turn (each card at its cost, an Enhance or an
     Accelerate cost within this turn's points plus the Bonus Play Point if unused).
   - A play survives if its card is in some set using at least B − SLACK.

   | rule | retention in the bucket (134) | moves cut in the bucket | retention over all 348 | moves cut over all |
   |---|---|---|---|---|
   | budget, slack 0 | 89.6% | 5.9% | 93.4% | 4.4% |
   | budget, slack 1 | 98.5% | 1.0% | 98.9% | 0.7% |
   | budget, slack 2 | 100% | 0.5% | 100% | 0.3% |

   - **It saves almost nothing.** Plays are only a fifth of the legal moves at wide decisions, and most plays do
     fit a full-budget set.
   - Where it does cut at slack 0, it loses the strongest tier's play 23% of the time (60 decisions touched).
   - Spending every play point is not what the strongest tier does: it holds cards and points.

## Reading

- **The breadth in the Ramp mirror is the discard choices.** They are 57% of the legal moves at wide decisions,
  and the bucket where the tiers disagree most. The next rule is still about discards, not plays.
- **Who discards what:**

  | | discards | the cheapest card in hand | the dearest card in hand | mean rank (0 cheapest, 1 dearest) |
  |---|---|---|---|---|
  | the strongest tier (this data) | 159 | 36% | 21% | 0.38 |
  | Salem (his Ramp-mirror games, analysis/xprune) | 94 | 45% | 5% | 0.23 |

  - Both discard Vorlalai and its Depths of the Eld Blades most.
  - Then the strongest tier discards Erntz (15) and Burnite (12); Salem discards Roar of Prominence (13) and
    Dragonewt Promoter (7).
  - Which is right is the open question (the architecture thread 17:40Z). The +xprune confirmation gate (52.4%
    pooled, passing) leans Salem's way, but does not settle it.
- **A next step, not done:** a position that separates the two habits directly. A wide discard decision where the
  strongest tier discards a big card and Salem's rule would keep it, played out both ways on many seeds.
