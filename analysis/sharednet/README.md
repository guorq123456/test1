# Shared value net: transfer test T1 (2026-10-29)

Condition: 对手卡表已知（牌序、手牌未知）— the opponent's deck list is known (order and hand not).

Why (the architecture thread 2026-10-29 02:30Z): the deck search has to judge decks by playing them, and the cheap
bot it can afford (mcts:100+plan, the hand-written score) misjudges some decks. A position score shared by every deck
would fix that; the first question is whether a value net already trained on one or two decks helps on set-10 decks it
never saw.

## Set-up

- Tool: `svsim/tools/deckgate.py` (a7a9d62). A pair is one deal of one ordered non-mirror matchup of the field: X plays
  deck a against Y playing b from both seats, then Y plays a against X playing b (4 games, one seed). The 42 ordered
  matchups of the 7 decks in turn, by offset (each block of 7 plays every deck once as a and once as b).
- Field: `fields/B-r1.txt`, search B's 7 incumbents after round 1 (claude/deck-search 241da436), all set-10 pool. Of
  each deck's ~30 distinct cards, 25-33 are new to either net.
- Y = `mcts:100+plan` (hand-written score). X = `mcts:N+plan+setnet=NET+netmid+netany` (+netany: the net scores every
  game, a7a9d62).
- Time match (the gate's rule, once): 12 pairs at N = 100, seeds 85890000 on (`t1/time-*.jsonl`): CPU per searched
  decision X / Y = 1.833 (net-mid-ramp-t) -> N 55, 2.028 (net-nm3g3f-elf-nem) -> N 49. Over the 300 pairs the ratio
  came out 1.14-1.21 (the 12-pair measure under-corrected; the rule adjusts once, so N stayed): X had 14-21% more CPU.
- 300 fixed pairs per arm (1200 games), bank 85800000 + k, the same seeds for every arm (paired).
- The architecture thread's prediction, registered before the run: the better of the two nets 48%-54%; above 52% with
  probability 0.4.

## Results (X's score, 95% interval over pairs)

| arm | X | score | CPU per step X / Y |
|---|---|---|---|
| 1 (registered) | net-mid-ramp-t, N 55 | 22.5% ± 2.1% | 46 / 39 ms |
| 2 (registered) | net-nm3g3f-elf-nem, N 49 | 23.0% ± 2.3% | 44 / 38 ms |
| 3 (added after) | 1 + `+netclip` | 23.0% ± 2.2% | 46 / 38 ms |
| 4 (added after) | 2 + `+netclip` | 25.5% ± 2.3% | 43 / 38 ms |

Paired differences (same seeds): arm 2 - arm 1 +0.5% ± 3.1%; arm 3 - arm 1 +0.5% ± 2.1%; arm 4 - arm 2 +2.5% ± 2.8%.

By the deck X played (arm 1 / 2 / 3 / 4): forest 19 / 16 / 15 / 20%, sword 44 / 47 / 47 / 45%, rune 9 / 16 / 11 / 16%,
dragon 21 / 20 / 23 / 20%, abyss 23 / 8 / 22 / 17%, haven 11 / 15 / 13 / 20%, portal 31 / 39 / 32 / 41% (about 86
pairs each, ± 4-8%). Logs with every line: `t1/*.log`; every game: `t1/*.jsonl`.

Both registered arms are far below the prediction: both nets lose to the hand-written score on unseen decks, by
about 27 points.

## Why +netclip (arms 3, 4)

A card's input is its static row standardized with the training cards' mean and std (learn.setnet). A column that
never varied in training has std ~1e-3, so a new card reads 1000-5000 standard deviations there (craft_sword,
hook_on_engage, countdown, type_amulet for the ramp-t net; craft_sword, hook_on_earth_rite, kw_aura for NM3), against
at most 12 (ramp-t) and 84 (NM3) on the nets' own cards. `+netclip` (c80f691) clips each column to the range of the
net's own cards (its own cards unchanged, bit for bit). It changed nothing measurable: the inputs blowing up is not
why the nets fail here.

## Control: the tool and +netany on the net's own pairing

`fields/control-elf-nem.txt` (elf-t and nemesis-t, the 2026-10-07 lists), seeds 85810000 on:
- C1: X = mcts:49+plan+setnet=net-nm3g3f-elf-nem+netmid (no +netany: its own pairing), 100 pairs: 58.2% ± 4.7%
  (elf-t 50.0%, nemesis-t 66.5%). The net helps on the decks it was trained on, through the same tool.
- C2: the same with +netany, the first 20 pairs: every pair's points and move counts identical to C1 (20 / 20).

So T1's result is the nets', not the tool's.
