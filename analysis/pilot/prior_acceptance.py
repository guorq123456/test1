"""Salem's four positions (analysis/resource-value/acceptance.py on claude/deck-search; his verdicts of 2026-10-31)
asked of a move prior instead of a value net: at each position, the prior's probability of the first step of
Salem's line against the first step of the bot's line (the prior ranks single moves, so a line is judged by its
first move; item 1's bot line is ending the turn). Pre-registered pass for this branch (analysis/pilot/PRIOR.md):
item 2, P(锅) > P(光). The other three are reported, not scored. Measurement only; the external deck enters no
search, self-play or training. Condition: 对手卡表已知（牌序、手牌未知）.

    python analysis/pilot/prior_acceptance.py analysis/scaling/models/prior-pilot-rune-dfm-ft-t05.npz
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import svsim.tools.arena  # noqa: E402,F401  (card scripts)
from svsim.cards import deckcode  # noqa: E402
from svsim.cards.pool import POOL  # noqa: E402
from svsim.core.actions import EndTurn  # noqa: E402
from svsim.core.engine import apply, legal_actions, new_game  # noqa: E402
from svsim.learn.setpolicy import load_cached  # noqa: E402
from svsim.tools.arena import make_agent  # noqa: E402
from svsim.ui.text import describe  # noqa: E402

DS = Path("/home/claude/test1/.wt/ds")                   # claude/deck-search (the lists live there)
REF = (ROOT if (ROOT / "analysis/deckbuild/blind-test/external/dfm-2026-10-31.txt").exists() else DS) \
    / "analysis/deckbuild/blind-test/external/dfm-2026-10-31.txt"
ROSTER = (ROOT if (ROOT / "analysis/deckbuild/blind-test/league5/roster.txt").exists() else DS) \
    / "analysis/deckbuild/blind-test/league5/roster.txt"
DECK = "dfm/RUNE-ユーリ"
# (name, opponent, seed, deck goes first, turn, Salem's first step, the bot's first step); as acceptance.py ITEMS
ITEMS = [
    ("第一局第3回合：零嘴做4土 > 空过", "bot/T1-SWORD-1", 85981131, True, 3, "使用「暴食的零嘴」，模式 1", None),
    ("第二局第3回合：先锅后光 > 先光后锅", "bot/T1-ABYSS-1", 85981161, True, 3, "使用「魔女的炼金炉」", "使用「智慧光辉」"),
    ("第三局第4回合：先打物证 > 先打解谜旋律", "g3/g3-P1-ABYSS-nocturne", 85981441, False, 4,
     "使用「神域的物证」", "使用「解谜旋律」"),
    ("第一局第7回合：琪可打骑士 > 先下迷人怪兽", "bot/T1-SWORD-1", 85981131, True, 7,
     "「玛纳利亚文书官·琪可」攻击敌方场上的「骑士」", "使用「迷人怪兽」"),
]


def read_seeds(path) -> dict:
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            label, _, code = line.rpartition("|")
            out[label.strip()] = deckcode.decode_deck(code.strip())[2]
    return out


def position(opp_label, seed, first, turn):
    """acceptance.position: the league deal replayed, both sides mcts:100+plan, to the deck's turn."""
    ref, ros = read_seeds(REF), read_seeds(ROSTER)
    for seat in (0, 1):
        cards = [None, None]
        cards[seat], cards[1 - seat] = [POOL[i] for i in ref[DECK]], [POOL[i] for i in ros[opp_label]]
        state = new_game(cards[0], cards[1], seed=seed)
        if (state.first == seat) != first:
            continue
        agents = [None, None]
        agents[seat] = make_agent("mcts:100+plan", 2 * seed + seat)
        agents[1 - seat] = make_agent("mcts:100+plan", 2 * seed + 1 - seat + 7919)
        while not (state.turn == turn and state.active == seat and state.phase.name == "MAIN"):
            apply(state, agents[state.active].act(state, legal_actions(state)))
        return state, seat
    raise ValueError("no such seat")


def fingerprint(state, seat):
    me = state.players[seat]
    return sorted(c.defn.card_id for c in me.hand), sorted(c.defn.card_id for c in me.field), me.pp, me.leader_hp


def main():
    prior = load_cached(sys.argv[1])
    passed = None
    for name, opp, seed, first, turn, salem, bot in ITEMS:
        state, seat = position(opp, seed, first, turn)
        acts = legal_actions(state)
        state.players[seat].deck_name = DECK
        p = prior.priors(state, acts)
        mass = {}
        for a, q in zip(acts, p):
            mass[describe(state, a)] = mass.get(describe(state, a), 0.0) + float(q)
        ps = sum(q for d, q in mass.items() if salem in d)
        pb = mass.get(describe(state, next(a for a in acts if isinstance(a, EndTurn))), 0.0) if bot is None \
            else sum(q for d, q in mass.items() if bot in d)
        top = sorted(mass.items(), key=lambda kv: -kv[1])[:5]
        ok = ps > pb
        if "先锅后光" in name:
            passed = ok
        print(f"{'过' if ok else '没过'}  {name}：Salem 的第一步 {ps:.3f}，bot 的第一步 {pb:.3f}   位置 {fingerprint(state, seat)}")
        print("    先验最高的五步：" + "；".join(f"{d} {q:.3f}" for d, q in top))
    print("预先登记的一题（先锅后光）：", "过" if passed else "没过")


if __name__ == "__main__":
    main()
