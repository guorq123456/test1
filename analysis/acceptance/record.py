"""Write the acceptance library's position files (run once; the files are then the positions).

The four replay points (analysis/resource-value/acceptance.py on claude/deck-search, Salem's verdicts of 2026-10-31)
are recorded by replaying that script's recipe once with the current engine: the league deal, both sides
mcts:100+plan, up to the deck's turn. The chosen actions are stored as (index in legal_actions, description), and
from then on the position is rebuilt by applying them; no search runs again.

The bunny board (analysis/pilot/salem_board_2026_11_01.py --accept) is built by builders.bunny_board; its fingerprint
is stored per deal.

    python analysis/acceptance/record.py --dfm DFM_LIST --roster ROSTER     # the two list files of claude/deck-search

Only the needed lists are written into the position files; the list files are not copied. Checks only: these
positions never enter search, self-play or training.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lib  # noqa: E402
from lib import apply, describe, legal_actions, new_game  # noqa: E402
from svsim.cards import deckcode  # noqa: E402

DECK = "dfm/RUNE-ユーリ"
SOURCE = "analysis/resource-value/acceptance.py on claude/deck-search; Salem's verdicts of 2026-10-31 22:45Z-23:03Z"
# (id, title, opponent, seed, deck goes first, turn, Salem's line, the bot's line, kind) as acceptance.py ITEMS
ITEMS = [
    ("rune-g1t3-snack", "第一局第3回合：零嘴做4土 > 空过", "bot/T1-SWORD-1", 85981131, True, 3,
     ["使用「暴食的零嘴」，模式 1"], [], "资源"),
    ("rune-g2t3-pot", "第二局第3回合：先锅后光 > 先光后锅", "bot/T1-ABYSS-1", 85981161, True, 3,
     ["使用「魔女的炼金炉」", "使用「智慧光辉」"], ["使用「智慧光辉」", "使用「魔女的炼金炉」"], "资源"),
    ("rune-g3t4-evidence", "第三局第4回合：先打物证再启动 > 先打解谜旋律再启动", "g3/g3-P1-ABYSS-nocturne", 85981441, False, 4,
     ["使用「神域的物证」", "启动「神域的物证」"], ["使用「解谜旋律」", "启动「神域的物证」"], "资源"),
    ("rune-g1t7-tico", "第一局第7回合：琪可打骑士+魔弹 > 怪兽打骑士+魔弹+琪可打脸", "bot/T1-SWORD-1", 85981131, True, 7,
     ["「玛纳利亚文书官·琪可」攻击敌方场上的「骑士」", "使用「玛纳利亚魔弹」", "使用「迷人怪兽」"],
     ["使用「迷人怪兽」", "「迷人怪兽」攻击敌方场上的「骑士」", "使用「玛纳利亚魔弹」", "「玛纳利亚文书官·琪可」攻击敌方主战者"],
     "打脸还是解场"),
]
BUNNY_REASON = ("「他的两只怪送不掉就不能出双顾问回血，单顾问只能回两滴血，他打过两张抽二钢铁所以不撞是一个稳定叫杀，而撞了不是」"
                "（Salem 2026-11-01 14:18Z）")


def codes(path) -> dict:
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            label, _, code = line.rpartition("|")
            out[label.strip()] = code.strip()
    return out


def record_replay(deck_code, opp_code, seed, first, turn):
    """acceptance.position's recipe, keeping the actions: (seat, [(index, description)], state)."""
    from svsim.tools.arena import make_agent
    decks = [lib.cards(deck_code), lib.cards(opp_code)]
    for seat in (0, 1):
        cards = [None, None]
        cards[seat], cards[1 - seat] = decks
        state = new_game(cards[0], cards[1], seed=seed)
        if (state.first == seat) != first:
            continue
        agents = [None, None]
        agents[seat] = make_agent("mcts:100+plan", 2 * seed + seat)
        agents[1 - seat] = make_agent("mcts:100+plan", 2 * seed + 1 - seat + 7919)
        actions = []
        while not (state.turn == turn and state.active == seat and state.phase.name == "MAIN"):
            acts = legal_actions(state)
            a = agents[state.active].act(state, acts)
            actions.append([acts.index(a), describe(state, a)])
            apply(state, a)
        return seat, actions, state
    raise ValueError("no such seat")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dfm", required=True)
    ap.add_argument("--roster", required=True)
    ap.add_argument("--out", default=str(lib.POSITIONS))
    args = ap.parse_args()
    dfm, roster = codes(args.dfm), codes(args.roster)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for pid, title, opp, seed, first, turn, salem, bot, kind in ITEMS:
        seat, actions, state = record_replay(dfm[DECK], roster[opp], seed, first, turn)
        pos = {"id": pid, "title": title, "kind": kind, "source": SOURCE,
               "deck": DECK, "deck_code": dfm[DECK], "opponent": opp, "opponent_code": roster[opp],
               "external": "dfm lists are EXTERNAL (Salem 「隔离训练」): checks only",
               "rebuild": {"kind": "replay", "seed": seed, "seat": seat, "first": first, "turn": turn,
                           "recorded_with": "mcts:100+plan both sides (acceptance.py's recipe), once", "actions": actions},
               "fingerprint": lib.fingerprint(state, seat),
               "salem": {"line": salem, "reason": None}, "wrong": [{"line": bot, "who": "the bot (mcts:100+plan)"}],
               "scorings": ["turn_end", "mid_turn", "prior", "handset"], "copies": 40, "reseed": "before_line",
               "tier": "unassigned"}
        (out / f"{pid}.json").write_text(json.dumps(pos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(pid, len(actions), "actions", pos["fingerprint"])
    seeds = list(range(86040000, 86040005))
    bunny = {"id": "haven-bunny-board-2026-11-01", "title": "Salem 2026-11-01 兔子教盘面：不撞 > 全撞", "kind": "叫杀",
             "source": "analysis/pilot/salem_board_2026_11_01.py --accept (Salem's screenshot, rebuilt by hand)",
             "deck": "dfm/HAVEN-ユーリ", "deck_code": dfm["dfm/HAVEN-ユーリ"], "opponent": DECK, "opponent_code": dfm[DECK],
             "external": "dfm lists are EXTERNAL (Salem 「隔离训练」): checks only; Salem's list is close to DFM's 兔子主教",
             "rebuild": {"kind": "builder", "function": "bunny_board", "line_function": "bunny_line", "seeds": seeds},
             "fingerprint": [], "salem": {"line": "keep", "reason": BUNNY_REASON},
             "wrong": [{"line": "all", "who": "trading all four bunnies"}],
             "scorings": ["handset"], "copies": 8, "reseed": "after_line",
             "note": "scored from Salem's (主教) side, hand-set evaluation only for now",
             "tier": "unassigned"}
    import builders
    for s in seeds:
        st, seat = builders.bunny_board(bunny, s)
        bunny["fingerprint"].append(lib.fingerprint(st, seat))
    (out / f"{bunny['id']}.json").write_text(json.dumps(bunny, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(bunny["id"], bunny["fingerprint"][0])


if __name__ == "__main__":
    main()
