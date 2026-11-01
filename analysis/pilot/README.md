# A trained pilot for one hero deck (the architecture thread 2026-10-31 23:35Z)

Condition: 对手卡表已知（牌序、手牌未知）.

Why: Salem reviewed 4 bot-piloted games of a planning-heavy Rune deck; at the decisions he flagged the hand-set score
ties or differs by about 0.1. Deck-specific self-play value nets gave elf-t / ramp-t 15-20 points before (ramp-t 30%
-> 49%, elf-t's mid net +141 CR), and nets do not transfer to decks they never saw (sharednet T1). The question:
does a pilot trained for one deck play it better than the untrained mcts:100+plan, on that deck only?

## Recipe (the elf-t recipe on set-10 decks)

- Field `fields/bot-frozen7.txt`: the 7 bot decks of the blind test's league 5 (claude/deck-search
  analysis/deckbuild/blind-test/league5/roster.txt, labels bot/*). Hero **bot/T3-RUNE-1**; opponents the other 6.
- Self-play (`learn.scaledata play --pool fields/bot-frozen7.txt --hero bot/T3-RUNE-1`, mcts:100+plan both sides):
  every game the hero against one other deck drawn by random.Random("hero:seed:g"), the hero in seat g % 2.
  10 shards x 1000 games, base 85990000 stride 2 (k < 10); holdout 2 shards, base 85991000 stride 2.
- Encode (`scaledata encode`, v1; `midrows encode`) and `analysis/scaling/train_mid.py --shared --fresh` ->
  `net-pilot-rune-bot-g1` (both seats' rows: the net scores every position the hero's search meets).
- Gate, hero only (`svsim/tools/herogate.py`): X = the hero piloted by mcts:N+plan+setnet=NET+netmid+netany, the
  baseline = the hero piloted by mcts:100+plan, on the same deals and seats against the same opponents
  (mcts:100+plan, the same agent seeds); pair k = the k-th opponent in turn on deal 85992000 + k, both seats, 300
  pairs; N time-matched once (24 pairs from 85992900, BLAS on one thread). Reported: X, the baseline and the paired
  difference with its 95% interval, by opponent too.
- If g1 beats the baseline: one more generation (5000 self-play games with the net on the hero's side,
  `--hero-spec`, base 85993000), retrain, gate on bank 85994000.

Seeds 85990000-85999999 are this line's (allocated by the architecture thread).

## EXTERNAL: hero dfm/RUNE-ユーリ, isolated training for measurement only

Salem chose 「隔离训练」 on the decision card (2026-10-31 23:18Z, relayed by the architecture thread 23:4xZ): the
external pro list may be self-play trained **for measurement only**. Isolation: its models are named
`net-pilot-rune-dfm-*`; never in a deck search, never in 陪练台 / the web models, never installed. The same recipe and
settings as the bot hero, so that the two lifts compare; the same 6 opponents.

`fields/dfm-yuri-vs-bot6.txt`: the external pro list dfm/RUNE-ユーリ (claude/deck-search
analysis/deckbuild/blind-test/external/dfm-2026-10-31.txt) against the same 6 non-Rune bot decks. That file says its
decks never enter a search, a self-play pool or training data; Salem's 「隔离训练」 allows this one isolated training,
for measurement. The commands, with this line's seeds:

    F=analysis/pilot/fields/dfm-yuri-vs-bot6.txt H=dfm/RUNE-ユーリ
    python -m svsim.learn.scaledata play --pool $F --hero $H --base 85995000 --stride 2 --shards 0 10 \
        --per-shard 1000 --spec mcts:100+plan --workers 4 --every 500 --out runs/pilot-dfm/rec
    python -m svsim.learn.scaledata play --pool $F --hero $H --base 85996000 --stride 2 --shards 0 2 \
        --per-shard 1000 --spec mcts:100+plan --workers 4 --every 500 --out runs/pilot-dfm/holdout
    # encode + midrows encode + train_mid.py --shared --fresh -> net-pilot-rune-dfm-g1
    python -m svsim.tools.herogate --hero $H --field $F --x "mcts:100+plan+setnet=NET+netmid+netany" \
        --base mcts:100+plan --opp mcts:100+plan --seed 85997900 --time 24 --out runs/pilot-dfm/time.jsonl
    python -m svsim.tools.herogate --hero $H --field $F --x "mcts:N+plan+setnet=NET+netmid+netany" \
        --base mcts:100+plan --opp mcts:100+plan --seed 85997000 --pairs 300 --out runs/pilot-dfm/gate-g1.jsonl
    # a second generation, if any: self-play base 85998000, gate bank 85999000

## Next, after the Rune pair reports: the Portal pair (Salem 2026-10-31 23:24Z; seeds the architecture thread 23:28Z)

DFM's 超越者 (人灭鱼, a fusion control deck with many decision points) gets the same isolated measurement, paired with
the bot's own 超越者 at an equal budget. Nothing starts until the Rune pair has reported. Seed bank 86000000-86009999:

| hero | field | self-play (10 shards, stride 2) | holdout (2) | gate bank | timing | gen-2 self-play | gen-2 gate |
|---|---|---|---|---|---|---|---|
| bot/T1-PORTAL-1 | fields/bot-frozen7.txt | 86000000 | 86001000 | 86002000 | 86002900 | 86003000 | 86004000 |
| dfm/PORTAL-MingiGod (EXTERNAL) | fields/dfm-portal-vs-bot6.txt | 86005000 | 86006000 | 86007000 | 86007900 | 86008000 | 86009000 |

The DFM Portal hero is EXTERNAL as the DFM Rune one: measurement only, models `net-pilot-portal-dfm-*`, never a deck
search, 陪练台 / the web models or an install.

The Rune pair's layout, for reference: bot/T3-RUNE-1 85990000 / 85991000 / gate 85992000 / timing 85992900 / gen 2
85993000, 85994000; dfm/RUNE-ユーリ (EXTERNAL, run in the architecture thread's container) 85995000 / 85996000 /
gate 85997000 / timing 85997900 / gen 2 85998000, 85999000.

## Result, g1 (bot/T3-RUNE-1)

- Self-play (mcts:100+plan both sides, 2.05 CPU s a game, about 7000 games an hour on 4 workers): the hero scores
  25.9% (holdout 25.6%); against Portal 12%, Sword 18%, Abyss 25%, Forest 27%, Haven 32%, Dragon 42%.
- `net-pilot-rune-bot-g1`: train_mid.py --shared --fresh on the 10 shards (turn ends 138677 rows, mid-turn thinned to
  as many), 15 epochs, best 11; validation (key split) log loss turn end 0.461, mid-turn 0.440 (start 1.104).
- Time match (24 pairs from 85992900, BLAS on one thread): X / baseline CPU 1.561 -> **N 64** (at N = 100: X 31.2%,
  baseline 22.9%, paired +8.3% ± 15.2%).
- Gate (300 pairs, bank 85992000, X = mcts:64+plan+setnet=net-pilot-rune-bot-g1+netmid+netany, baseline
  mcts:100+plan, opponents mcts:100+plan): **X 18.2% ± 3.1%, baseline 25.5% ± 3.4%, paired difference -7.3% ± 3.8%
  (95% -11.1% to -3.6%)**. By opponent: Forest -10.0, Sword -5.0, Dragon -5.0, Abyss -8.0, Haven -9.0, Portal -7.0
  (± 8-11 each). CPU X 44 ms, baseline 41 ms a searched decision: ratio 1.059.
- g1 does not beat the baseline, so no second generation (the line's rule). Logs in `logs/`.
- The check without time matching (the architecture thread 01:28Z; its reading registered before: a paired difference
  >= 0 or an interval reaching above 0 = the cost is the problem, an interval wholly below 0 = the values are worse):
  the same 300 pairs on bank 85992000 with X at N = 100: **X 17.2% ± 3.1%, baseline 25.5% ± 3.4%, paired -8.3% ±
  3.7% (95% -12.0% to -4.7%)**. By opponent: Forest -10.0, Sword +1.0, Dragon -8.0, Abyss -11.0, Haven -12.0, Portal
  -10.0 (± 7-12 each). CPU X 58 ms, baseline 41 ms: ratio 1.431. The whole interval is below 0: **the net's values
  are worse**, not only its cost (with 43% more CPU it still loses 8 points).

## The rule corrected: a second generation after all (the architecture thread 2026-11-01 01:40Z)

"Gen 2 only if g1 beats the baseline" was wrong: the precedent's own gen 1 lost too (analysis/scaling/README.md: the
10⁴ net against v2skx came to 44.3%, 40.7%-47.8%), and that line went on to a second generation "so the net plays its
own positions", then a third, 10⁵, a move prior. A fresh gen-1 net is exploited by the search on positions its pilot
never reached; self-play with the net is the correction. So, for the bot Rune hero:
1. Gen 2 self-play: `scaledata play --pool fields/bot-frozen7.txt --hero bot/T3-RUNE-1 --hero-spec
   "mcts:64+plan+setnet=net-pilot-rune-bot-g1+netmid+netany" --spec mcts:100+plan`, base 85993000 stride 2, 10 shards
   x 1000.
2. The same encode; a fresh net on gen 1 + gen 2 (20 shards; gen 1's data stays in), the same settings, holdout
   85991000/2 -> `net-pilot-rune-bot-g2`.
3. Time match once (24 pairs from 85994900), gate 300 pairs on 85994000 against mcts:100+plan, as for g1.

Registered before any game (the architecture thread): g2 closes at least half of g1's gap (paired difference >= -3.6)
with probability 0.5; g2 beats the baseline (interval above 0) 0.2. If g2 is still clearly below, the next lever is
the precedent's first step (a per-deck refit of the turn-end evaluator as the base the net corrects), not more
generations. The DFM hero gets the same second generation in the architecture thread's container (85998000 /
85999000).

## Result, g2 (bot/T3-RUNE-1)

- Gen-2 self-play (the hero piloted by mcts:64 + net g1, opponents mcts:100+plan, 1.8 CPU s a game, about 7950 games
  an hour on 4 workers): the hero scored 17.2%.
- `net-pilot-rune-bot-g2`: fresh, on gen 1 + gen 2 (20 shards), the same settings; 12 epochs; validation log loss
  turn end 0.419, mid-turn 0.400 (g1: 0.461, 0.440).
- Time match (24 pairs from 85994900): CPU X / baseline 1.488 -> **N 67** (at N = 100: -6.2% ± 16.0%).
- Gate (300 pairs, bank 85994000, X = mcts:67+plan+setnet=net-pilot-rune-bot-g2+netmid+netany): **X 34.2% ± 4.0%,
  baseline 25.8% ± 3.5%, paired difference +8.3% ± 4.3% (95% +4.0% to +12.6%)**. By opponent: Forest +22.0 (± 9.4),
  Sword +0.0, Dragon +8.0, Abyss +2.0, Haven +15.0 (± 10.2), Portal +3.0. CPU X 48 ms, baseline 40 ms a searched
  decision: **ratio 1.190** (the rule matches once; X has 19% more CPU here).
- Against the registered predictions: g2 closes at least half of g1's gap (>= -3.6), probability 0.5: yes; g2 beats
  the baseline (interval above 0), probability 0.2: yes. One generation of the net playing its own positions turned
  -7.3 into +8.3.

- **Equal CPU** (the same 300 pairs on bank 85994000, X at N 56): **X 31.3% ± 3.9%, baseline 25.8% ± 3.5%, paired
  +5.5% ± 4.4% (95% +1.1% to +9.9%)**; CPU X 42 ms, baseline 40 ms: ratio 1.050. By opponent: Forest +17.0 (± 10.7),
  Sword +1.0, Dragon +5.0, Abyss +5.0, Haven +8.0, Portal -3.0 (± 8.6-13.2). The gain holds at equal CPU, smaller
  (+5.5 against +8.3 with 19% more).

## Next (the architecture thread 2026-11-01 03:29Z): the equal-CPU check, then a third generation

- Equal CPU: the same 300 pairs on bank 85994000 with X at N 56 (= 67 / 1.19), the report to Salem resting on it.
- Gen 3 for the bot Rune hero instead of the mirror arm (a Rune mirror game costs about 2.6 times as much; the mirror
  arm is on hold for both heroes): hero `mcts:67+plan+setnet=net-pilot-rune-bot-g2+netmid+netany`, opponents
  mcts:100+plan, 10 shards x 1000 at base 86020000 stride 2; a fresh net on gen 1 + 2 + 3 (30 shards), the same
  settings -> `net-pilot-rune-bot-g3`; time match once on 86021900; gate 300 pairs on 86021000 against mcts:100+plan.
  Seeds 86020000-86024999 are the bot hero's gens 3-4; 86025000-86029999 the DFM hero's.
- Registered (the architecture thread, before any game): g3 beats g2's paired difference on its own bank 0.55; g3
  beats the baseline 0.7.

## Result, g3 (bot/T3-RUNE-1)

- Gen-3 self-play (the hero piloted by mcts:67 + net g2, opponents mcts:100+plan, 2.2 CPU s a game, about 6400 games
  an hour on 4 workers): the hero scored **32.5%** (gen 2's self-play with g1: 17.2%); Dragon 52%, Haven 40%, Forest
  36%, Abyss 25%, Sword 23%, Portal 18%.
- `net-pilot-rune-bot-g3`: fresh on gens 1-3 (30 shards), the same settings, 19 epochs; validation log loss turn end
  0.443, mid-turn 0.424 (not comparable with g2's: the validation games include gen 3's).
- Time match (24 pairs from 86021900): CPU 1.513 -> **N 66** (at N = 100: +8.3% ± 16.3%).
- Gate (300 pairs, bank 86021000, X = mcts:66+plan+setnet=net-pilot-rune-bot-g3+netmid+netany): **X 37.5% ± 3.9%,
  baseline 26.2% ± 3.5%, paired +11.3% ± 4.4% (95% +6.9% to +15.7%)**. By opponent: Forest +16.0, Sword +14.0,
  Dragon +13.0, Abyss +8.0, Haven +9.0, Portal +8.0 (± 9.4-12.1): above the baseline against all six. CPU X 47 ms,
  baseline 41 ms: **ratio 1.130**.
- Against the registered predictions: g3 beats g2's paired difference on its own bank (+8.3), 0.55: yes; g3 beats the
  baseline, 0.7: yes.
- **Equal CPU** (the same 300 pairs on bank 86021000, X at N 58 = 66 / 1.13): **X 34.2% ± 4.1%, baseline 26.2% ±
  3.5%, paired +8.0% ± 4.2% (95% +3.8% to +12.2%)**; CPU X 44 ms, baseline 42 ms: ratio 1.052. By opponent: Forest
  +12.0, Sword +5.0, Dragon +14.0, Abyss +3.0, Haven +12.0, Portal +2.0 (± 8.7-12.2).

| generation | gate N (ratio) | paired | equal CPU N (ratio) | paired at equal CPU |
|---|---|---|---|---|
| g1 | 64 (1.059) | -7.3 ± 3.8 | (N 100: -8.3 ± 3.7) | - |
| g2 | 67 (1.190) | +8.3 ± 4.3 | 56 (1.050) | +5.5 ± 4.4 |
| g3 | 66 (1.130) | +11.3 ± 4.4 | 58 (1.052) | +8.0 ± 4.2 |

The bot Rune hero's gen 4 is deferred (its bank 86022000-86024999 reserved); next, the Portal pair (the architecture
thread 06:10Z): the same recipe with generations, gen 1 expected to lose, a gate every generation, a time match once
each, an equal-CPU check whenever the in-gate ratio is above 1.08; DFM and bot alternating. Gen-3 banks: 86030000-
86034999 the bot Portal hero, 86035000-86039999 the DFM one (self-play +0, gate +1000, timing +1900).


## Result, Portal pair gen 1: dfm/PORTAL-MingiGod (EXTERNAL, measurement only)

EXTERNAL: a pro list (Salem 「隔离训练」 2026-10-31 23:18Z), isolated. Measurement only: never in deck search, the
trainer or web models, never installed. Field `fields/dfm-portal-vs-bot6.txt` (the DFM Portal list + the 6 non-Portal
bot decks). Condition: 对手卡表已知（牌序、手牌未知）.

- Self-play: 10 shards x 1000 from 86005000 (stride 2), both sides mcts:100+plan, 2.8 CPU s a game; holdout 2 x 1000
  from 86006000. The hero scored **36.2%** in self-play (holdout 35.5%). Records in `data/portal-dfm/`, logs in
  `logs/portal-dfm/`.
- The first background task stopped at the 2-hour limit during the holdout (self-play complete); the rest ran as a
  separate chunk (the generation script now has stages `play` and `rest`, each under the limit). Not a restart.
- `net-pilot-portal-dfm-g1`: train_mid.py --shared --fresh on the 10 shards (turn ends 169578 rows, mid-turn 623108
  thinned at 0.272), holdout 86006000/86006002. Best epoch 3 of 7 (early stop): valid brier 0.185, log loss 0.546
  (bot rune g1: 0.148 / 0.451 at epoch 11). The Portal games are harder to value from these inputs, or the net
  overfits sooner.
- Time match (24 pairs from 86007900): ratio 1.358 → N 74.
- Gate (300 pairs, bank 86007000, X = mcts:74+plan+setnet=net-pilot-portal-dfm-g1+netmid+netany, baseline and
  opponents mcts:100+plan): **X 28.7% ± 3.8%, baseline 34.3% ± 4.1%, paired -5.7% ± 4.6% (95% -10.3% to -1.0%)**;
  CPU X 57 ms, baseline 48 ms: ratio 1.182. By opponent: Forest -13.0, Sword -2.0, Rune +9.0, Dragon -20.0,
  Abyss -11.0, Haven +3.0 (± 8.1-14.2).
- **Equal CPU** (the same bank, N 63 = 74 / 1.182): **X 27.2% ± 3.7%, baseline 34.3%, paired -7.2% ± 4.6% (95%
  -11.7% to -2.6%)**; ratio 1.053. By opponent: Forest -10.0, Sword -8.0, Rune +0.0, Dragon -26.0, Abyss -4.0,
  Haven +5.0.
- Gen 1 loses, as expected (bot rune g1: -7.3 ± 3.8). Next: the bot Portal hero's g1, then gen 2 for both.

## Result, Portal pair gen 1: bot/T1-PORTAL-1

Field `fields/bot-frozen7.txt` (the 7 bot decks; the hero against the other 6). Condition: 对手卡表已知（牌序、手牌未知）.

- Self-play: 10 shards x 1000 from 86000000 (stride 2), both sides mcts:100+plan, 2.3 CPU s a game; holdout 2 x 1000
  from 86001000. The hero scored **67.4%** in self-play (holdout 67.2%). Records in `data/portal-bot/`, logs in
  `logs/portal-bot/`. Run as two planned chunks (`play`, then `rest`).
- `net-pilot-portal-bot-g1`: train_mid.py --shared --fresh on the 10 shards (turn ends 149103 rows, mid-turn 501615
  thinned at 0.297), holdout 86001000/86001002. Best epoch 9 of 13: valid brier 0.160, log loss 0.482.
- Time match (24 pairs from 86002900): ratio 1.383 → N 72.
- Gate (300 pairs, bank 86002000, X = mcts:72+plan+setnet=net-pilot-portal-bot-g1+netmid+netany): **X 61.3% ± 4.0%,
  baseline 67.8% ± 3.8%, paired -6.5% ± 4.5% (95% -11.0% to -2.0%)**; CPU X 57 ms, baseline 52 ms: ratio 1.097. By
  opponent: Forest -6.0, Sword -4.0, Rune -10.0, Dragon +1.0, Abyss -16.0, Haven -4.0 (± 8.2-13.4).
- **Equal CPU** (the same bank, N 66 = 72 / 1.097): **X 57.3% ± 4.0%, baseline 67.8%, paired -10.5% ± 4.7% (95%
  -15.2% to -5.8%)**; ratio 1.034. By opponent: Forest -11.0, Sword +0.0, Rune -10.0, Dragon -5.0, Abyss -23.0,
  Haven -14.0.
- Gen 1 loses, as expected. Next: gen 2 for both Portal heroes (timing seeds gate bank + 900: DFM 86009900, bot
  86004900; the architecture thread 10:39Z agreed).

The bot Rune hero's gen 4 moved to the architecture thread's container (10:39Z: self-play 86022000 with mcts:66 + net
g3, fresh on gens 1-4, time 86023900, gate 86023000), from this branch's records and net g3; not run here. Their
DFM Rune g3 at equal CPU (N 50, ratio 1.113): +17.8 ± 4.0 (7.3% → 25.2%), commit 0dfe3573 on claude/pilot-dfm.

| hero | generation | gate N (ratio) | paired | equal CPU N (ratio) | paired at equal CPU |
|---|---|---|---|---|---|
| dfm/PORTAL-MingiGod (EXTERNAL) | g1 | 74 (1.182) | -5.7 ± 4.6 | 63 (1.053) | -7.2 ± 4.6 |
| bot/T1-PORTAL-1 | g1 | 72 (1.097) | -6.5 ± 4.5 | 66 (1.034) | -10.5 ± 4.7 |
| dfm/PORTAL-MingiGod (EXTERNAL) | g2 | 63 (1.218) | +14.8 ± 4.7 | 52 (1.094) | +10.3 ± 4.9 |
| bot/T1-PORTAL-1 | g2 | 78 (1.169) | +2.8 ± 4.1 | 67 (1.091) | +5.0 ± 4.4 |
| dfm/PORTAL-MingiGod (EXTERNAL) | g3 | 59 (1.173) | +16.2 ± 4.8 | 50 (1.067) | +18.8 ± 4.7 |

## Result, Portal pair gen 2: dfm/PORTAL-MingiGod (EXTERNAL, measurement only)

Condition: 对手卡表已知（牌序、手牌未知）.

- Self-play: 10 shards x 1000 from 86008000, the hero piloted by mcts:74 + net-pilot-portal-dfm-g1 (g1's gate N),
  opponents mcts:100+plan; 3.3 CPU s a game. The hero scored **30.7%** (gen 1's self-play: 36.2%). Records in
  `data/portal-dfm/rec-g2/`.
- Process: the container restarted once during self-play (the chunk re-created, resuming from the part file); a
  later chunk's outer `timeout` killed the script but not its inner `timeout` child, so two processes briefly wrote
  the last shard's part file: 11 games twice, identical apart from "date" and "cpu", and the shard is keyed by g, so
  the shard is sound. The generation script now gives every step what is left of one chunk deadline, with no outer
  timeout.
- `net-pilot-portal-dfm-g2`: fresh on gens 1 + 2 (20 shards; turn ends 332466 rows, mid-turn 1239889 thinned at
  0.268), holdout 86006000/86006002. Best epoch 7 of 11: valid brier 0.173, log loss 0.519 (g1: 0.185 / 0.546).
- Time match (24 pairs from 86009900): ratio 1.600 → N 63.
- Gate (300 pairs, bank 86009000, X = mcts:63+plan+setnet=net-pilot-portal-dfm-g2+netmid+netany): **X 47.8% ± 4.3%,
  baseline 33.0% ± 3.9%, paired +14.8% ± 4.7% (95% +10.1% to +19.6%)**; CPU X 57 ms, baseline 47 ms: ratio 1.218.
  By opponent: Forest +22.0, Sword +5.0, Rune +15.0, Dragon +26.0, Abyss +11.0, Haven +10.0 (± 9.4-13.8): above the
  baseline against all six.
- **Equal CPU** (the same bank, N 52 = 63 / 1.218): **X 43.3% ± 4.2%, baseline 33.0%, paired +10.3% ± 4.9% (95%
  +5.5% to +15.2%)**; ratio 1.094 (still a little above 1.08: one check per generation, as the rule says; the
  difference at a ratio of 1.0 would be a little smaller). By opponent: Forest +5.0, Sword +7.0, Rune +12.0, Dragon
  +20.0, Abyss +8.0, Haven +10.0.

## Result, Portal pair gen 2: bot/T1-PORTAL-1

Condition: 对手卡表已知（牌序、手牌未知）.

- Self-play: 10 shards x 1000 from 86003000, the hero piloted by mcts:72 + net-pilot-portal-bot-g1, opponents
  mcts:100+plan; 2.6 CPU s a game. The hero scored **56.8%** (gen 1's self-play: 67.4%). Records in
  `data/portal-bot/rec-g2/`.
- `net-pilot-portal-bot-g2`: fresh on gens 1 + 2 (turn ends 302467 rows, mid-turn 1040101 thinned at 0.291), holdout
  86001000/86001002; the first chunk's deadline came after epoch 1 and the second chunk resumed from the checkpoint
  ("resumed_after_epoch": 1). Best epoch 11 of 15: valid brier 0.172, log loss 0.510 (g1: 0.160 / 0.482 on its own
  holdout rows; the gen-2 rows are not the same mix, so the two are not directly comparable).
- Time match (24 pairs from 86004900): ratio 1.274 → N 78.
- Gate (300 pairs, bank 86004000, X = mcts:78+plan+setnet=net-pilot-portal-bot-g2+netmid+netany): **X 69.5% ± 3.8%,
  baseline 66.7% ± 4.0%, paired +2.8% ± 4.1% (95% -1.3% to +6.9%)**; CPU X 61 ms, baseline 52 ms: ratio 1.169. By
  opponent: Forest +3.0, Sword -2.0, Rune -1.0, Dragon +15.0, Abyss -4.0, Haven +6.0 (± 7.7-11.3).
- **Equal CPU** (the same bank, N 67 = 78 / 1.169): **X 71.7% ± 3.8%, baseline 66.7%, paired +5.0% ± 4.4% (95%
  +0.6% to +9.4%)**; ratio 1.091. By opponent: Forest +2.0, Sword +4.0, Rune +3.0, Dragon +15.0, Abyss -1.0, Haven
  +7.0.
- The smaller budget scoring higher is noise between two readings on the same deals (2.2 points apart, each ± 4.1-4.4).
  Read together: gen 2 is a few points above the baseline, from -6.5 / -10.5 at gen 1. The bot Portal hero is already
  strong (the baseline 66.7%), so there is less room than for the DFM hero (baseline 33.0%).

## Result, Portal pair gen 3: dfm/PORTAL-MingiGod (EXTERNAL, measurement only)

Condition: 对手卡表已知（牌序、手牌未知）. Gen-3 bank 86035000-86039999.

- Self-play: 10 shards x 1000 from 86035000, the hero piloted by mcts:63 + net-pilot-portal-dfm-g2 (g2's gate N),
  opponents mcts:100+plan; 3.5 CPU s a game; two chunks. The hero scored **50.1%** (gen 2: 30.7%, gen 1: 36.2%).
  Records in `data/portal-dfm/rec-g3/`.
- `net-pilot-portal-dfm-g3`: fresh on gens 1-3 (30 shards; turn ends 508770 rows, mid-turn 1919012 thinned at
  0.265), holdout 86006000/86006002. Best epoch 6 of 10: valid brier 0.178, log loss 0.529 (the holdout rows are gen-1
  games, so this does not compare across generations).
- Time match (24 pairs from 86036900): ratio 1.685 → N 59.
- Gate (300 pairs, bank 86036000, X = mcts:59+plan+setnet=net-pilot-portal-dfm-g3+netmid+netany): **X 51.2% ± 4.3%,
  baseline 35.0% ± 3.9%, paired +16.2% ± 4.8% (95% +11.4% to +20.9%)**; CPU X 57 ms, baseline 48 ms: ratio 1.173. By
  opponent: Forest +11.0, Sword +12.0, Rune +22.0, Dragon +36.0, Abyss +3.0, Haven +13.0 (± 9.9-12.6).
- **Equal CPU** (the same bank, N 50 = 59 / 1.173): **X 53.8% ± 4.3%, baseline 35.0%, paired +18.8% ± 4.7% (95%
  +14.1% to +23.6%)**; ratio 1.067. By opponent: Forest +17.0, Sword +16.0, Rune +26.0, Dragon +36.0, Abyss +8.0,
  Haven +10.0.
- g2 was +14.8 / +10.3 on its own bank (86009000). On g3's deals at the same N 50: g2 X 50.5%. **g3 − g2 = +3.3 ± 4.8**
  (analysis/pilot/paired.py). The move prior step follows in PRIOR-PORTAL.md.
