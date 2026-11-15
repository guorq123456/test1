"""Item 6b: Salem's first five turns of real games, replayed in the simulator; the bot chooses at the start of each
turn and its line is compared with his (pre-registration and results: REALGAME.md).

Check only, never training. Inputs, all from /mnt/project-files/shadowverse/salem-games/tracker/: the raw breadcrumb
files and games.jsonl. Needs a checkout of the tracker (branch claude/svwb-tracker, tools/svwb_tracker) for its
parser, and the DFM list file (external, comparison only).

    python analysis/process/realgame_6b.py --tracker DIR [--lists FILE] [--games 3,5] [--out PATH.jsonl] [--workers N]
"""
import argparse
import collections
import itertools
import json
import os
import sys
import types
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import svsim.tools.arena  # noqa: F401  (card scripts)
from svsim.cards import deckcode
from svsim.cards.pool import POOL
from svsim.core import effects as E
from svsim.core.actions import (
    Attack,
    EndTurn,
    Evolve,
    Mulligan,
    PlayCard,
    UseBonusPP,
)
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.state import Phase
from svsim.tools.arena import make_agent

DATA = Path("/mnt/project-files/shadowverse/salem-games/tracker")
DFM = Path("/home/claude/test1/.wt/ds/analysis/deckbuild/blind-test/external/dfm-2026-10-31.txt")  # claude/deck-search
SALEM_LIST = {"兔子主教": "dfm/HAVEN-ユーリ", "增幅证据三轴土": "dfm/RUNE-ユーリ"}
M = "analysis/scaling/models"
BOT = {"增幅证据三轴土": f"mcts:30+plan+setnet={M}/net-pilot-rune-dfm-g5.npz+netmid+netany"
                     f"+puct={M}/prior2-pilot-rune-dfm-ft-t05.npz:2:1",
       "兔子主教": "mcts:100+plan"}
SEED_BASE = 86300000          # seed bank for 6b positions: 86300000 + 100 * game + turn


# --- the tracker's parser, with three outputs added (turn starts, raw turn per move, the event list) --------------

def load_tracker(d):
    path = Path(d) / "svwb_tracker.py"
    src = path.read_text(encoding="utf-8")
    patches = [
        ('''        if s == "me":
            my_turns += 1
        else:
            opp_turns += 1
''', '''        if s == "me":
            my_turns += 1
        else:
            opp_turns += 1
        g.setdefault("turn_starts", []).append({"side": s, "raw_turn": my_turns if s == "me" else opp_turns, "t": t})
'''),
        ('moves.append({"t": x["t"], "side": s, "turn": my_turns if s == "me" else opp_turns,',
         ('moves.append({"t": x["t"], "side": s, "raw_turn": my_turns if s == "me" else opp_turns, '
          '"turn": my_turns if s == "me" else opp_turns,')),
        ('    n_body = len(body)\n', '    n_body = len(body)\n    g["_body"] = body\n'),
        ('    g["moves"] = moves\n', ('    g["moves"] = moves\n    g["_side_of"] = list(side_of)\n'
                                    '    g["_preplay_of"] = list(preplay_of)\n')),
    ]
    for old, new in patches:
        assert old in src, f"tracker parser changed; patch not applied: {old[:40]!r}"
        src = src.replace(old, new)
    mod = types.ModuleType("svwb_tracker_6b")
    mod.__file__ = str(path)
    exec(compile(src, str(path), "exec"), mod.__dict__)
    return mod


def load_games(tracker_dir):
    T = load_tracker(tracker_dir)
    d = str(tracker_dir) + "/"
    cards = T.load_cards(d + "cards_zh.json")
    arch = T.load_archetypes(d + "archetypes.json")
    cfg = {"my_min_seen": 3, "my_min_score": 0.75, "opp_min_seen": 2, "opp_min_score": 0.6, "opp_margin": 0.15}
    games = [T.analyze(s, cards, {}, arch, cfg) for s in T.segment(T.load_raw(DATA / "raw"))]
    ref = [json.loads(line) for line in open(DATA / "games.jsonl", encoding="utf-8")]
    by = {round(r["start"], 1): i for i, r in enumerate(ref)}
    out = []
    for g in games:
        i = by.get(round(g["start"], 1))
        if i is not None:
            out.append((i, g, ref[i]))
    archetypes = json.loads(Path(d + "archetypes.json").read_text(encoding="utf-8"))["decks"]
    return sorted(out, key=lambda x: x[0]), archetypes


def norm(cid):
    s = str(cid)
    if s.startswith("7"):
        s = "1" + s[1:]
    if len(s) == 8 and s[-1] in "13":
        s = s[:-1] + {"1": "0", "3": "2"}[s[-1]]
    return int(s)


def reliable(r):
    return not r["mirror"] and not r["partial"] and not any("回合号" in w or "回合数" in w for w in r["warnings"])


# --- Salem's hand at the start of each of his turns ---------------------------------------------------------------

def hands(g):
    """{turn: {"hands": [Counter...], "decide": t}} for Salem's turns, or (None, why). A hand is the cards he held at
    his first action of that turn (after the turn's draw). Several hands = several mulligans fit the record."""
    body, side, pre = g["_body"], g["_side_of"], g["_preplay_of"]
    t0 = body[0]["t"]
    me_in = [(x["t"], norm(x["cid"])) for k, x in enumerate(body)
             if x["kind"] == "hand" and side[k] == "me" and pre[k] is None and x["cid"] != "0"]
    pre_in = [(x["t"], norm(x["cid"])) for k, x in enumerate(body)
              if x["kind"] == "hand" and pre[k] is not None and x["cid"] != "0"]
    first_play = min([x["t"] for x in body if x["kind"] == "play"], default=1e18)
    initial = [c for t, c in me_in if t - t0 <= 3.0]
    if len(initial) != 4:
        return None, f"起手不是 4 张（{len(initial)}）"
    rest = [(t, c) for t, c in me_in if t - t0 > 3.0]
    starts = [t["t"] for t in g.get("turn_starts", []) if t["side"] == "me"]
    first_me = starts[0] if starts else first_play
    cand = [(t, c) for t, c in rest if t < min(first_me, first_play) - 0.3]
    repl = [(t, c) for t, c in cand if t - cand[0][0] <= 1.0] if cand else []
    entries = [e for e in rest if e not in repl] + repl
    seen_in = {c for t, c in me_in}
    plays = []
    for m in g["moves"]:
        if m["side"] != "me" or m["kind"] != "出牌":
            continue
        c = norm(m["cid"])
        h = c - 2 if str(c).endswith("2") and (c - 2) in seen_in | set(initial) else c
        if h in seen_in or h in initial or not (str(c).startswith("9") or str(c).endswith("2")):
            plays.append((m["t"], h))
    # a card played with none in hand: its reveal just before the play was the draw (drawn and played at once)
    have = collections.Counter(initial)
    ev = sorted([(t, 0, c) for t, c in entries] + [(t, 1, c) for t, c in plays])
    extra = []
    for t, kind, c in ev:
        if kind == 0:
            have[c] += 1
        elif have[c] > 0:
            have[c] -= 1
        else:
            r = [p for p in pre_in if p[1] == c and 0 <= t - p[0] <= 5.0]
            if r:
                extra.append(r[-1])
    entries += extra
    n_ret = len(repl)
    need, cin, cout = collections.Counter(), collections.Counter(), collections.Counter()
    for t, kind, c in sorted([(t, 0, c) for t, c in entries] + [(t, 1, c) for t, c in plays]):
        (cin if kind == 0 else cout)[c] += 1
        need[c] = max(need[c], cout[c] - cin[c])
    init = collections.Counter(initial)
    for c in need:
        if need[c] > init[c]:
            return None, "打出的牌比进手的多"
    cards = sorted(init)
    alts = [collections.Counter({c: k for c, k in zip(cards, ks) if k})
            for ks in itertools.product(*[range(need[c], init[c] + 1) for c in cards])
            if sum(init[c] - k for c, k in zip(cards, ks)) == n_ret]
    if not alts:
        return None, "换牌张数和起手对不上"
    opp_starts = [t["t"] for t in g.get("turn_starts", []) if t["side"] == "opp"]
    out = {}
    for turn in sorted({m["turn"] for m in g["moves"] if m["side"] == "me"} | set(range(1, 6))):
        acts = [m["t"] for m in g["moves"] if m["side"] == "me" and m["turn"] == turn and m["kind"] != "入场（效果）"]
        if acts:
            decide = min(acts) - 0.05
        else:
            continue          # no action that turn: no line to compare
        base = collections.Counter()
        for t, c in entries:
            if t < decide:
                base[c] += 1
        for t, c in plays:
            if t < decide:
                base[c] -= 1
        hs = []
        for a in alts:
            h = collections.Counter(base)
            h.update(a)
            h = +h
            if h not in hs:
                hs.append(h)
        out[turn] = {"hands": hs, "decide": decide, "n_ret": n_ret, "opp_before": sum(1 for t in opp_starts if t < decide)}
    return out, None


# --- replay in the simulator ---------------------------------------------------------------------------------------

def read_lists(path):
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            label, _, code = line.rpartition("|")
            out[label.strip()] = deckcode.decode_deck(code.strip())[2]
    return out


CLS = {"精灵": 1, "皇家护卫": 2, "巫师": 3, "龙族": 4, "梦魇": 5, "主教": 6, "超越者": 7}


def opp_list(r, archetypes):
    named = [d for d in archetypes if d["name"] == r["opp_deck"]]
    pool = named or [d for d in archetypes if CLS.get(d["cls"]) == r["opp_cls"]]
    d = pool[0]
    ids = [int(c) for c, n in d["cards"].items() for _ in range(n)]
    return ids, d["label"] + ("" if named else "（未知套路，按职业取第一副）")


def card_of(st, uid):
    for p in st.players:
        for z in (p.hand, p.field):
            for c in z:
                if c.uid == uid:
                    return c
    return None


def set_hand(st, pi, want):
    """Make player pi's hand exactly `want` (Counter of card ids): return extras to the deck, take missing cards from
    the deck, create the rest (created cards, or a card not in the list)."""
    p = st.players[pi]
    have = collections.Counter(c.defn.card_id for c in p.hand)
    created = 0
    for c in list(p.hand):
        if have[c.defn.card_id] > want[c.defn.card_id]:
            p.hand.remove(c)
            p.deck.append(c)
            have[c.defn.card_id] -= 1
    for cid, n in want.items():
        for _ in range(n - have[cid]):
            c = next((x for x in p.deck if x.defn.card_id == cid), None)
            if c is not None:
                p.deck.remove(c)
                p.hand.append(c)
            elif cid in POOL:
                E.add_to_hand(st, pi, POOL[cid])
                created += 1
    st.rng.shuffle(p.deck)
    return created


def do_move(st, pi, m, notes):
    cid = norm(m["cid"])
    base = cid - 2 if str(cid).endswith("2") else cid
    p = st.players[pi]
    if m["kind"] == "出牌":
        if not any(c.defn.card_id in (cid, base) for c in p.hand):
            if str(cid).startswith("9") and pi == 0:
                return               # a summoned token logged as a play
            c = next((x for x in p.deck if x.defn.card_id in (base, cid)), None)
            if c is not None:
                p.deck.remove(c)
                p.hand.append(c)
            elif base in POOL:
                E.add_to_hand(st, pi, POOL[base])
            else:
                return
        for attempt in range(3):
            acts = [a for a in legal_actions(st) if isinstance(a, PlayCard)
                    and card_of(st, a.uid) is not None and card_of(st, a.uid).defn.card_id in (cid, base)]
            if acts:
                apply(st, st.rng.choice(acts))
                return
            if attempt == 0 and any(isinstance(a, UseBonusPP) for a in legal_actions(st)):
                apply(st, UseBonusPP())
                continue
            c = next((x for x in p.hand if x.defn.card_id in (cid, base)), None)
            if c is None or p.pp >= 10:
                break
            p.pp = min(10, max(p.pp, c.cost))
            notes["forced_pp"] += 1
        notes["unplayable"] += 1
    elif m["kind"] in ("进化", "超进化"):
        sup = m["kind"] == "超进化"
        acts = [a for a in legal_actions(st) if isinstance(a, Evolve) and a.super_ == sup
                and card_of(st, a.uid) is not None and card_of(st, a.uid).defn.card_id in (cid, base)]
        if acts:
            apply(st, st.rng.choice(acts))
        else:
            notes["evolve_skipped"] += 1


def build(r, g, rec, k, archetypes, lists, seed):
    """The state at Salem's (player 0) first action of his turn k, or (None, why)."""
    salem = lists[SALEM_LIST[r["my_deck"]]]
    opp, opp_label = opp_list(r, archetypes)
    first = 0 if r["first"] else 1
    st = new_game([POOL[i] for i in salem], [POOL[i] for i in opp], seed=seed, first=first)
    while st.phase == Phase.MULLIGAN:
        apply(st, Mulligan(()))
    notes = collections.Counter()
    moves = collections.defaultdict(list)
    for m in g["moves"]:
        if m["side"] in ("me", "opp") and m["kind"] in ("出牌", "进化", "超进化"):
            moves[(m["side"], m["turn"])].append(m)
    for _ in range(40):
        if st.phase == Phase.OVER:
            return None, "重演中对局结束了", notes
        pi = st.active
        j = st.players[pi].turns_taken
        if pi == 0:
            if j in rec and len(rec[j]["hands"]) == 1:
                notes["created"] += set_hand(st, 0, rec[j]["hands"][0])
            if j == k:
                return st, opp_label, notes
            for m in moves[("me", j)]:
                do_move(st, 0, m, notes)
        else:
            for m in moves[("opp", j)]:
                do_move(st, 1, m, notes)
        if st.active == pi and st.phase != Phase.OVER:
            apply(st, EndTurn())
    return None, "没走到这一回合", notes


def bot_line(st, spec, seed):
    agent = make_agent(spec, seed)
    line = []
    for _ in range(60):
        if st.phase == Phase.OVER or st.active != 0:
            break
        a = agent.act(st, legal_actions(st))
        if isinstance(a, PlayCard):
            line.append(("出牌", card_of(st, a.uid).defn.card_id))
        elif isinstance(a, Evolve):
            line.append(("超进化" if a.super_ else "进化", card_of(st, a.uid).defn.card_id))
        elif isinstance(a, Attack):
            line.append(("攻击", None))
        apply(st, a)
        if isinstance(a, EndTurn):
            break
    return line


def board(st, pi):
    return [(c.defn.card_id, c.atk, c.life, c.evolved) for c in st.players[pi].field]


def run_one(job):
    gi, k, r, g, rec, archetypes, lists = job
    seed = SEED_BASE + 100 * gi + k
    try:
        os.nice(10)
    except (OSError, AttributeError):
        pass
    st, info, notes = build(r, g, rec, k, archetypes, lists, seed)
    salem = [(m["kind"], norm(m["cid"])) for m in g["moves"]
             if m["side"] == "me" and m["turn"] == k and m["kind"] in ("出牌", "进化", "超进化")]
    out = {"game": gi + 1, "turn": k, "deck": r["my_deck"], "opp": r["opp_deck"], "first": r["first"],
           "salem": salem, "notes": dict(notes)}
    if st is None:
        out["skip"] = info
        return out
    out.update({"opp_list": info, "hand": sorted(c.defn.card_id for c in st.players[0].hand),
                "my_board": board(st, 0), "opp_board": board(st, 1),
                "pp": st.players[0].pp, "max_pp": st.players[0].max_pp, "ep": st.players[0].ep})
    out["bot"] = bot_line(st.clone(), BOT[r["my_deck"]], seed)
    return out


def key(line):
    """Cards played, created cards included (an alternate form counts as its base card), and evolve targets, ignoring
    order and attacks: the registered agreement rule."""
    def base(c):
        return c - 2 if str(c).endswith("2") else c
    return sorted((k, base(c)) for k, c in line if k in ("出牌", "进化", "超进化"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", required=True)
    ap.add_argument("--games", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--lists", default=str(DFM), help="the DFM list file (external, comparison only)")
    a = ap.parse_args()
    games, archetypes = load_games(a.tracker)
    lists = read_lists(Path(a.lists))
    jobs, dropped = [], collections.Counter()
    only = {int(x) for x in a.games.split(",")} if a.games else None
    for gi, g, r in games:
        if only and gi + 1 not in only:
            continue
        if not reliable(r) or r["my_deck"] not in SALEM_LIST or r["first"] is None:
            continue
        rec, err = hands(g)
        if err:
            dropped[err] += 1
            continue
        for k in range(1, 6):
            if k not in rec:
                dropped["这回合没出牌"] += 1
            elif len(rec[k]["hands"]) != 1:
                dropped["换牌不确定"] += 1
            else:
                jobs.append((gi, k, r, g, rec, archetypes, lists))
    print(f"{len(jobs)} 个回合；没做的：{dict(dropped)}", flush=True)
    with Pool(a.workers) as pool:
        res = pool.map(run_one, jobs, chunksize=1)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in res)
    done = [x for x in res if "bot" in x]
    agree = [x for x in done if key(x["salem"]) == key(x["bot"])]
    print(f"做成 {len(done)}，跳过 {len(res) - len(done)}：{collections.Counter(x.get('skip') for x in res if 'skip' in x)}")
    for deck in SALEM_LIST:
        d = [x for x in done if x["deck"] == deck]
        s = [x for x in d if key(x["salem"]) == key(x["bot"])]
        print(f"{deck}：一致 {len(s)}/{len(d)}")
    print(f"总计一致 {len(agree)}/{len(done)}")


if __name__ == "__main__":
    main()
