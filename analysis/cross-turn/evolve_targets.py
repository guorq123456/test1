"""What there was to evolve when Salem held, against when Salem evolved, and what came next.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> analysis/mirror-regression/salem_games.json \
        [--probes analysis/mirror-regression/evolve_probes.json --results v2s=FILE ...]

For each of Salem's turns in evolve_probes.json (evolve_hold / evolve_use),
the evolution targets of the turn, by role (cards.dragon / neutral scripts):
- payoff: an evolution with a lasting or card-advantage effect: Burnite
  (super: the crest), Erntz (evolved: 8 to the enemy leader every turn),
  Lumiore & Argente (super: draw 3), Vorlalai (Depths of the Eld Blades: 1, or 3
  on a super), Normagdala (the Fanfare again), Kimika (the Fanfare again);
- plain: a follower whose evolution only adds stats (Lyria, Dragonewt
  Promoter, Zooey, Sagatsumatsu, tokens).
Classes of the turn: "收益牌可进化" (a payoff follower could be evolved at some
decision of the turn), "收益牌在手、本回合够不着" (none could, but one is in
hand), "只有普通随从" (neither). For held turns, whether Salem evolved a
payoff follower in the next two own turns. With --results (check.py output
for evolve_probes.json), the bot's pass rate by class. With --selfplay LABEL
FILE instead, the same held / used table for both seats of self-play records
(each class's share among held and used turns, and the class's hold rate).
"""
import json
import re
import sys
from collections import Counter, defaultdict

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import Evolve, from_dict
from svsim.core.engine import apply, legal_actions
from svsim.tools import records

PAYOFF = {"焦灰的安纳提玛·班德奈特", "约束的《正义》·伊兰翠", "金银绚烂·璐米欧儿&雅尔贞特", "古旧天刀·波菈莱",
          "禁牙的变貌·诺玛格达拉", "满面笑容的烹饪·琪米卡"}


def name(c):
    return c.defn.name_zh or c.defn.name


def salem_turns(rec):
    acts = [from_dict(a) for a in rec["actions"]]
    st = records.start(rec)
    i, out = 0, []
    while i < len(acts) and not st.over:
        if st.active != 0 or type(acts[i]).__name__ == "Mulligan":
            apply(st, acts[i])
            i += 1
            continue
        start, turn = i, []
        while i < len(acts) and st.active == 0 and not st.over:
            turn.append((st.clone(), acts[i]))
            apply(st, acts[i])
            i += 1
        out.append((start, turn))
    return out


def classify(turn):
    targets = set()
    for s, _ in turn:
        for a in legal_actions(s):
            if isinstance(a, Evolve):
                targets.add(name(s.on_field(a.uid)))
    hand = {name(c) for c in turn[0][0].players[0].hand}
    if targets & PAYOFF:
        return "收益牌可进化", targets
    if hand & PAYOFF:
        return "收益牌在手、本回合够不着", targets
    return "只有普通随从", targets


def player_turns(rec, seats=(0, 1)):
    """(seat, the turn's (state, action) pairs) for every turn of the given seats that did not win the game."""
    acts = [from_dict(a) for a in rec["actions"]]
    st = records.start(rec)
    out, cur, seat = [], [], None
    for a in acts:
        if st.phase.name != "MAIN":
            apply(st, a)
            continue
        if seat is None:
            seat = st.active
        cur.append((st.clone(), a))
        apply(st, a)
        if st.over or st.active != seat:
            if seat in seats and not (st.over and st.winner == seat):
                out.append((seat, cur))
            cur, seat = [], None
        if st.over:
            break
    return out


def turn_row(turn):
    """The held / used table's row for one turn where evolving was possible, else None."""
    legal = [(s, a) for s, _ in turn for a in legal_actions(s) if isinstance(a, Evolve)]
    used = [a for _, a in turn if isinstance(a, Evolve)]
    if not legal and not used:
        return None
    cls, _ = classify_seat(turn)
    normal_only = not any(a.super_ for _, a in legal)
    return {"held": not used, "class": cls, "normal_only": normal_only}


def classify_seat(turn):
    me = turn[0][0].active
    targets = set()
    for s, _ in turn:
        for a in legal_actions(s):
            if isinstance(a, Evolve):
                targets.add(name(s.on_field(a.uid)))
    hand = {name(c) for c in turn[0][0].players[me].hand}
    if targets & PAYOFF:
        return "收益牌可进化", targets
    if hand & PAYOFF:
        return "收益牌在手、本回合够不着", targets
    return "只有普通随从", targets


def table(label, rows):
    held = [r for r in rows if r["held"]]
    used = [r for r in rows if not r["held"]]
    print(f"\n{label}：能进化的回合 {len(rows)} 个，忍住 {len(held)}（{len(held) / len(rows):.0%}）")
    for k in ("收益牌可进化", "收益牌在手、本回合够不着", "只有普通随从"):
        h = sum(r["class"] == k for r in held)
        u = sum(r["class"] == k for r in used)
        print(f"  {k:<14} 占忍住 {h / max(len(held), 1):.0%}  占用了 {u / max(len(used), 1):.0%}  这一格的忍住率 {h}/{h + u}"
              f"（{h / max(h + u, 1):.0%}）")
    h = sum(r["normal_only"] for r in held)
    u = sum(r["normal_only"] for r in used)
    print(f"  {'只能普通进化':<14} 占忍住 {h / max(len(held), 1):.0%}  占用了 {u / max(len(used), 1):.0%}  这一格的忍住率 {h}/{h + u}"
          f"（{h / max(h + u, 1):.0%}）")


def main():
    if "--selfplay" in sys.argv:              # the same table for both seats of self-play records
        import gzip
        i = sys.argv.index("--selfplay")
        label, path = sys.argv[i + 1], sys.argv[i + 2]
        opener = gzip.open if path.endswith(".gz") else open
        rows = []
        with opener(path, "rt", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    for _, turn in player_turns(json.loads(line)):
                        r = turn_row(turn)
                        if r:
                            rows.append(r)
        table(label, rows)
        return
    games = json.load(open(sys.argv[1], encoding="utf-8"))["records"]
    probes_path = sys.argv[sys.argv.index("--probes") + 1] if "--probes" in sys.argv else None
    probes = json.load(open(probes_path, encoding="utf-8"))["positions"] if probes_path else []
    by_game = defaultdict(dict)
    for gid, rec in games.items():
        for start, turn in salem_turns(rec):
            by_game[gid][start] = turn
    rows = {}
    for p in probes:
        turns = by_game[p["game"]]
        starts = sorted(turns)
        k = starts.index(p["at"])
        cls, targets = classify(turns[p["at"]])
        evolved = [name(s.on_field(a.uid)) for s, a in turns[p["at"]] if isinstance(a, Evolve)]
        later = [name(s.on_field(a.uid)) for st_ in starts[k + 1:k + 3] for s, a in turns[st_] if isinstance(a, Evolve)]
        rows[p["id"]] = {"category": p["category"], "class": cls, "evolved": evolved, "later": later,
                         "later_payoff": bool(set(later) & PAYOFF)}
    salem_rows = []
    for gid, rec in games.items():
        for seat, turn in player_turns(rec, (0,)):
            r = turn_row(turn)
            if r:
                salem_rows.append(r)
    table("Salem（全部能进化的回合，含当回合没有探针的）", salem_rows)
    for cat in ("evolve_hold", "evolve_use"):
        sub = [r for r in rows.values() if r["category"] == cat]
        c = Counter(r["class"] for r in sub)
        print(f"\n{cat}（{len(sub)} 个回合）：" + "，".join(f"{k} {n}（{n / len(sub):.0%}）" for k, n in c.most_common()))
        if cat == "evolve_hold":
            for k in c:
                s2 = [r for r in sub if r["class"] == k]
                print(f"  {k}：之后两回合内进化了收益牌 {sum(r['later_payoff'] for r in s2)}/{len(s2)}")
        else:
            ev = Counter(("收益牌" if e in PAYOFF else "普通随从") for r in sub for e in r["evolved"])
            print("  Salem 进化的是：" + "，".join(f"{k} {n}" for k, n in ev.items()))
    for spec in [a for a in sys.argv if "=" in a and not a.startswith("--")]:
        label, path = spec.split("=", 1)
        ok = defaultdict(lambda: [0, 0])
        for line in open(path, encoding="utf-8"):
            m = re.match(r"(\S+)\s+(\d+)/(\d+)$", line.strip())
            if not m or m.group(1) not in rows:
                continue
            r = rows[m.group(1)]
            key = (r["category"], r["class"])
            ok[key][0] += int(m.group(2))
            ok[key][1] += int(m.group(3))
        print(f"\n{label} 的通过率，按目标类别：")
        for key in sorted(ok):
            a, n = ok[key]
            print(f"  {key[0]} / {key[1]}：{a}/{n}（{a / n:.0%}）")


if __name__ == "__main__":
    main()
