# Installed on Salem's Windows machine: 「最强」 level + strong package (lethal-clock evaluator + discard pruning)

Salem's choices: 「新增最强档」 (2026-10-10 01:45Z) and 「两样都装」 (2026-10-11 18:46Z), and 「装吧克！」 in the
local thread (2026-10-13 23:36Z). Checklist: analysis/install/WINDOWS_CHECKLIST.md §7 (3ba425e). Condition:
对手卡表已知（牌序、手牌未知）.

The arena checkout C:\claude\test1 (local/pairings-20261008) took b215e3d (merge a7fc7ff), then 3ba425e
(merge 7f2c751, code identical to 3ba425e, so the later speed rounds such as 0e038cb come too; the +lethal3 switches
are off by default). Then `strong_kc_xprune.py apply` ran. Every run went through `python -m svsim.tools.host`
(below normal, mask 0xffffe). The same steps were first rehearsed in a separate worktree (rehearsal/), with
identical results.

| step | result |
|---|---|
| check before | strong mcts:200+plan+learned+phased, max mcts:1043+plan+learned+phased, levels d1eb81d0…ea10, not installed, package digest 1e7bc6f8…5675 ok |
| cmp_roots before / after apply | 116 755a0bba6cfb1119729e19b4af0484d6a583854d678b1697cd91fb39f63596a6, both |
| golden_hash | five games equal to the 8bb28a8 Windows values |
| 最强 smoke (1 pair, seed 69900010) | both games finished |
| apply | before d1eb81d0896bb431dedba8ac511b157a5aff9f1b1f116c31174d20b381eaea10, after c0125dc5a06aaf7fa3f885ed6708c43df4e2f6a338c839834de00805376d9ea9, package ok |
| package smoke | first line `"ramp_ramp_ended_read_by": {"strong": "pkg-kc-ramp-ramp", "max": "installed"}`; 6 games decided; cut 1349 / 1395 / 3307 / 3252 (ramp), 64 / 302 (nemesis-t / pirate-t); OK |
| pytest test_web, test_learn, test_xprune, test_install_packages | 72 passed |
| | INSTALLED |
| check after | state installed, levels c0125dc5…9ea9 |

After this, `level-strong` is the new strong level (v2skx); the old one is v2s. ratings.json is unchanged.
The arena was not running, so nothing was restarted.

The b215e3d speed check is in analysis/speed/windows-r2/ (see its README).
