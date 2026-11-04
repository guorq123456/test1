# S1 / S1(b) data (saved at the pause, Salem 2026-10-29 11:21Z 「先暂停一会」; S1(b) k = 20..35 finished 15:54Z)

Condition: 对手卡表已知（牌序、手牌未知）.

- `rec/rec-<seed>.jsonl.gz`: learn.scaledata play records, 1000 games each, seed 85830000 + 2k.
  - k = 0..19 (85830000-85830038): S1, pool `fields/C-r0-pool.txt`, both sides mcts:100+plan.
  - k = 20..35 (85830040-85830070): S1(b), pool `fields/P2-pool.txt`, both sides mcts:100+plan (k = 28 was resumed
    after the pause from game 912, 「继续吧」 13:22Z; every shard checked: its 1000 deal keys seed·100003 + g, each once).
  - k = 36..59 (85830072-85830118): the RC line (Salem's computer), branch `claude/sharednet-p2-rc` commit fb7f3c9,
    `rec-p2/` (svsim 68e3190, an ancestor of this branch with the same engine, cards and search); not copied here.
    Checked here: 1000 deal keys per shard, each once, and the first 50 games' decks are pool_pair's draw.
- `ckpt-prior.npz`: learn.setpolicy fit's checkpoint of the shared move prior (S1 (i)), after epoch 3 (validation
  cross-entropy 1.3811 on the held-out decks' games; epochs 1-3: 1.3879, 1.3832, 1.3811); the same fit command
  with --checkpoint at this file resumes exactly.
- `cards-all.npz`: the static rows of every card in S1's turn-end, mid-turn and decision files (554 cards).

The encoded files (tok-, mid-, dec-) are not here: `scaledata encode`, `midrows encode` and `setpolicy encode` on
these records give them again.

- `rec-p3/rec-<seed>.jsonl.gz`: P3 self-play (the architecture thread 2026-10-29 19:45Z, Salem 19:44Z approved ten
  times the data), this container's share k = 160..179 (85830320-85830358), pool `fields/P3-pool.txt` (sha256
  51c34e1a...), both sides mcts:100+plan, code 48f96b4 and after (the same engine); 20 x 1000 games, each shard's
  deal keys checked once each, the first 30 games' decks pool_pair's draw. `play.log` the runs' log. The other
  shares: Salem's computer k = 60..79 (claude/sharednet-p3-rc), the architecture thread's container k = 180..259
  (claude/sharednet-p3-thread); stopped near 128000 games in all (the architecture thread 2026-10-30 00:52Z).
