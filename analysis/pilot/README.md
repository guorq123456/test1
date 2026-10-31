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

## Prepared, not run: hero dfm/RUNE-ユーリ

`fields/dfm-yuri-vs-bot6.txt`: the external pro list dfm/RUNE-ユーリ (claude/deck-search
analysis/deckbuild/blind-test/external/dfm-2026-10-31.txt) against the same 6 non-Rune bot decks. **It waits for
Salem's decision in the architecture thread.** That file says its decks never enter a search, a self-play pool or
training data; a pilot trained on this deck's self-play is such training data, so it needs Salem's explicit yes. An
isolated measurement only: never deck search, 陪练台 or a bot install. The commands, with this line's seeds:

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
