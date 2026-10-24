"""Learn when the player uses each card, from their games (Chinese output).

    python -m svsim.tools.timing <games folder or files> --deck rhino --opponent ramp

Counts the player's card timing and opening redraws (svsim.learn.timing),
prints them card by card with the redraw the AI would now make, and saves
the counts to svsim/learn/timing/<deck>-<opponent>.json, where the AI's
opening redraw (agents.mulligan) finds them.
"""
from __future__ import annotations

import argparse

from svsim.agents.mulligan import PLAYER_RULES
from svsim.cards import decks
from svsim.cards.pool import POOL
from svsim.learn.timing import EARLY, collect
from svsim.ui.session import DECKS
from svsim.ui.text import card_name


def load_games(paths: list[str]) -> list[dict]:
    """Every recorded game, finished or not (a resigned game shows the timing too)."""
    import json
    from pathlib import Path
    out = []
    for p in paths:
        files = sorted(Path(p).glob("**/*.json")) if Path(p).is_dir() else [Path(p)]
        for f in files:
            d = json.loads(f.read_text(encoding="utf-8"))
            rec = d.get("data", d).get("record", d.get("data", d))
            if isinstance(rec, dict) and len(rec.get("actions", [])) >= 10:
                out.append(rec)
    return out


def report(timing, say=print) -> None:
    cards = decks.build(DECKS[timing.deck][1])
    counts: dict = {}
    for c in cards:
        counts[c.card_id] = counts.get(c.card_id, 0) + 1
    total = sum(counts.values())
    baseline = sum(n * timing.early(cid) for cid, n in counts.items()) / total
    rules = PLAYER_RULES.get(timing.deck)
    say(f"{DECKS[timing.deck][0]} 对 {DECKS[timing.opponent][0]}：{timing.games} 局；"
        f"随便抽一张牌、前 {EARLY} 回合打出的平均机会 {baseline:.0%}")
    rows = []
    for cid in counts:
        s = timing.cards.get(cid)
        med = timing.median_turn(cid)
        first = timing.keep_chance(cid, 0, baseline, rules)
        second = timing.keep_chance(cid, 1, baseline, rules)
        rows.append((med if med is not None else 99, card_name(POOL[cid]), timing.early(cid),
                     sum(s.played) if s else 0, (s.kept[0] + s.kept[1]) if s else 0,
                     (s.redrawn[0] + s.redrawn[1]) if s else 0, first, second, med))
    for _, name, early, plays, kept, redrawn, first, second, med in sorted(rows):
        verdict = "留" if first >= 0.5 else "换"
        if first >= 0.5 and second < 0.5:
            verdict = "留一张"
        med_text = f"{med:4.1f}" if med is not None else "  - "
        say(f"  {name:14s} 打出 {plays:3d} 次，回合中位数 {med_text}，前 {EARLY} 回合打出 {early:4.0%}；"
            f"起手留 {kept} 换 {redrawn} → {verdict}（留下的把握 {first:.0%}）")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("games", nargs="+", help="game records (folders or files)")
    parser.add_argument("--deck", default="rhino")
    parser.add_argument("--opponent", default="ramp")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()
    timing = collect(load_games(args.games), args.deck, args.opponent)
    report(timing)
    if not args.no_save and timing.games:
        print("已保存到", timing.save())


if __name__ == "__main__":
    main()
