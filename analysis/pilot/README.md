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

## Next (the architecture thread 2026-11-01 03:29Z): the equal-CPU check, then a third generation

- Equal CPU: the same 300 pairs on bank 85994000 with X at N 56 (= 67 / 1.19), the report to Salem resting on it.
- Gen 3 for the bot Rune hero instead of the mirror arm (a Rune mirror game costs about 2.6 times as much; the mirror
  arm is on hold for both heroes): hero `mcts:67+plan+setnet=net-pilot-rune-bot-g2+netmid+netany`, opponents
  mcts:100+plan, 10 shards x 1000 at base 86020000 stride 2; a fresh net on gen 1 + 2 + 3 (30 shards), the same
  settings -> `net-pilot-rune-bot-g3`; time match once on 86021900; gate 300 pairs on 86021000 against mcts:100+plan.
  Seeds 86020000-86024999 are the bot hero's gens 3-4; 86025000-86029999 the DFM hero's.
- Registered (the architecture thread, before any game): g3 beats g2's paired difference on its own bank 0.55; g3
  beats the baseline 0.7.
