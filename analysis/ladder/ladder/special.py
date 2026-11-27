"""Special periods: periods whose new decks come from given lists only, with strategies of the players' own.

Two kinds ("style"):

**teams** (period 3; Salem's S27, 11-24 14:22Z and 14:47Z): a deck period in which each player picks one team of a
pro league round and hands in that team's seven decks, one per class, not one card changed, with strategies of their
own. Period 3: Premier Series 26-27 round 11, second half (11/18 JST): four teams, 28 lists
(decklists/ps11b-2026-11-18.txt).

How a player takes part (public/special-P3.md):
1. a 「选队」 submission (submission.json {"type": "选队", "team": <the team's name as listed>}, no other file): the
   team is theirs for the period if it still has room (first come, first served, in receipt order); one team per player
   and period, not changed afterwards;
2. seven 「新卡组」 submissions as in any deck period (S5), each one the team's list of its class (the same 40 cards; the
   code may list them in any order).

Room (A62): at most MAX_PLAYERS_PER_TEAM players per team, and the pool's own rule (pool.MAX_PER_LIST, locked) that at
most 2 active members hold one list. A team is open to a player only if every one of its seven lists can take one more
member once the claims already made are counted: for each class, the active members holding the list (members this
period's claimants entered for that class are counted through the claims, not twice) + the other claimants whose team
has the same list for that class + this one <= MAX_PER_LIST. So a claim, once accepted, is never stranded: its seven
decks fit. Lists shared by two teams (LVH and RC's forest list in period 3) and lists a pool member already holds count
against every team that has them.

**blueprints** (period 4; Salem 11-27): three given lists, 快攻妖精 (Forest), 跳费龙 (Dragon) and 兔子教 (Haven);
each player hands in at most one new deck of each (the slot rule's one per class, pool.NEW_DECKS_PER_CLASS), a
blueprint with at most its `max_changes` cards changed (7, 7, 6), counted by cards: changes = 40 - the number of
cards the deck and the blueprint share as multisets of card ids (2 X for 2 Y is 2). No team claim; other classes are
refused (public/special-P4.md). Per the spec's flags:
- "updates": False: no strategy updates this period (merged periods start at period 5). pool.py (locked) still calls
  period 4 merged; takes_updates() here is the rule the submission check, the collector and the opening go by;
- "admit": False: an accepted deck does not enter the pool (Salem: 「池子先看结果，再评估是否放进去」): no admit,
  ever, for a receipt of such a period (submit._admit refuses it), and the pool's same-list cap (MAX_PER_LIST) is not
  checked for it, so the blueprint as given is fine for every player;
- "eval": "players": the period's evaluation plays the players' members against each other's only (another tool;
  its seed range is "eval_seeds"), never on a frozen pool: no frozen pool is taken for it (freezes_pool()).

Nothing here changes the pool (pool.py is locked): the claims live in the submissions ledger, the decks of a teams
period enter through submit.admit like any deck period's.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

LADDER = Path(__file__).resolve().parents[1]

SPECIAL = {
    3: {"style": "teams", "decklists": "decklists/ps11b-2026-11-18.txt",
        "title": "职业联赛 Premier Series 26-27 第 11 节后半（11/18）"},
    4: {"style": "blueprints", "title": "三副蓝本：快攻妖精、跳费龙、兔子教", "kind_zh": "特殊期",
        "guide": "special-P4.md",
        "blueprints": {      # Salem 11-27, as he gave them: card id -> copies (each one passes submit.check_deck)
            "快攻妖精": {"craft": 1, "max_changes": 7, "cards": {
                10501110: 3, 10711120: 3, 11012110: 3, 10814120: 3, 10514120: 3, 11013310: 3, 11014110: 2,
                10503210: 3, 10811130: 3, 10514110: 2, 11012310: 3, 10914110: 3, 11013110: 3, 10814110: 3}},
            "跳费龙": {"craft": 4, "max_changes": 7, "cards": {
                10542120: 2, 10842120: 3, 10544120: 3, 10603210: 3, 10644110: 3, 10844120: 3, 10544110: 3,
                10644120: 3, 10543310: 3, 10042310: 3, 10503310: 3, 10944120: 3, 10744110: 3, 11044110: 2}},
            "兔子教": {"craft": 6, "max_changes": 6, "cards": {
                10062210: 3, 10861110: 3, 10863210: 1, 10863110: 3, 11062110: 2, 10061210: 2, 11062310: 3,
                10861120: 2, 11001110: 1, 11061110: 2, 11002110: 3, 10962120: 3, 11063310: 3, 10864120: 3,
                11064110: 3, 11063110: 3}},
        },
        "updates": False,                      # merged periods from period 5 (pool.py still says merged for 4)
        "admit": False,                        # accepted decks stay out of the pool for now
        "eval": "players",                     # the players' members against each other's, no frozen pool
        "eval_seeds": (96310000, 96410000)},   # the evaluation's range (96310000-96409999; SEEDS.md, the host)
}
MAX_PLAYERS_PER_TEAM = 2
NOT_IN_POOL = ("这一期收下的新卡组先不进池子（特殊期，Salem 定的）：不上天梯、不算 CR，期末只和别的选手这一期的卡组互打评测；"
               "以后进不进池子，Salem 看了结果再定")


def is_special(period: int) -> bool:
    return period in SPECIAL


def style(period: int) -> str | None:
    """The special period's kind: "teams" (period 3), "blueprints" (period 4); None for a period that isn't one."""
    spec = SPECIAL.get(period)
    if spec is None:
        return None
    return spec.get("style") or ("blueprints" if "blueprints" in spec else "teams")


def takes_updates(period: int) -> bool:
    """Strategy updates are received in `period`: the pool's rule (pool.takes_updates, locked), unless the period is
    a special one that takes none (period 4: merged periods start at 5, Salem 11-27)."""
    from ladder.pool import takes_updates as pool_takes
    return pool_takes(period) and SPECIAL.get(period, {}).get("updates", True)


def admits(period: int) -> bool:
    """An accepted new deck of `period` enters the pool (False in period 4: 「池子先看结果，再评估是否放进去」)."""
    return SPECIAL.get(period, {}).get("admit", True)


def freezes_pool(period: int) -> bool:
    """The special period's evaluation is played on the pool frozen at its end (period 3, A63), so the next period's
    opening freezes it first (tools/open_period.py). Period 4's is between the players only."""
    return is_special(period) and SPECIAL[period].get("eval", "frozen") == "frozen"


def kind_zh(period: int, default: str) -> str:
    """What the players are told the period is: 特殊期 for period 4 (the pool's kind is merged); else `default`."""
    return SPECIAL.get(period, {}).get("kind_zh", default)


def first_merged() -> int:
    """The first period that is merged and takes strategy updates (5: period 4 is special, Salem 11-27)."""
    from ladder.pool import MERGED_FROM
    n = MERGED_FROM
    while not takes_updates(n):
        n += 1
    return n


@lru_cache(maxsize=None)
def teams(period: int) -> dict:
    """{team: {craft: {"label", "code", "ids" (sorted card ids), "player"}}} of a special period's round."""
    from ladder import base
    from ladder.runner import load_deck
    if style(period) != "teams":
        raise ValueError(f"period {period} is not a special period with teams")
    spec = SPECIAL[period]
    out: dict = {}
    for line in (LADDER / spec["decklists"]).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        label, code, _round, team, player, *_ = line.split("|")
        deck = load_deck(code)
        craft = int(base.craft_of(deck))
        if craft in out.setdefault(team, {}):
            raise ValueError(f"{team} has two {craft} lists in {spec['decklists']}")
        out[team][craft] = {"label": label, "code": code, "ids": sorted(c.card_id for c in deck), "player": player}
    for team, by in out.items():
        if len(by) != 7:
            raise ValueError(f"{team} has {len(by)} lists, not 7")
    return out


def canonical(team, names) -> object:
    """The team name as the round writes it, for one written with stray spaces or in other letter case (11-24
    review: a claim is first come, first served, so a slip shouldn't cost a round trip); anything else unchanged."""
    if not isinstance(team, str):
        return team
    x = " ".join(team.split())
    return next((n for n in names if n == x), None) or next((n for n in names if n.casefold() == x.casefold()), team)


def all_team_names() -> set:
    """Every team of every special period with teams (precheck can't know the period)."""
    return set().union(*(teams(p) for p in SPECIAL if style(p) == "teams"))


def claims(lines: list, period: int) -> dict:
    """{player: (team, receipt id)}: the accepted 选队 receipts of the period, the first per player."""
    out = {}
    for l in lines:
        if (l.get("ev") == "receipt" and l.get("kind") == "team" and l.get("verdict") == "收下"
                and l.get("period") == period and l.get("player") not in out):
            out[l["player"]] = (l.get("team"), l["id"])
    return out


def room(team: str, player: str, period: int, pool, lines: list) -> list[str]:
    """Why `player` can't take `team` now ([] = they can)."""
    from ladder.pool import CRAFT_ZH, MAX_PER_LIST, list_key
    t = teams(period)
    made = {p: tm for p, (tm, _) in claims(lines, period).items() if p != player}
    on_team = sorted(p for p, tm in made.items() if tm == team)
    problems = []
    if len(on_team) >= MAX_PLAYERS_PER_TEAM:
        problems.append(f"{team} 已经有 {len(on_team)} 个选手选了（每队最多 {MAX_PLAYERS_PER_TEAM} 个）")
        return problems
    for craft, entry in sorted(t[team].items()):
        key = list_key(entry["ids"])
        sharing = [p for p, tm in made.items() if list_key(t[tm][craft]["ids"]) == key]
        held = [m for m in pool.active() if list_key(m.deck) == key
                and not (m.entry_period == period and m.owner in sharing and m.craft == craft)]
        if len(held) + len(sharing) + 1 > MAX_PER_LIST:
            problems.append(f"{team} 的{CRAFT_ZH[craft]}卡表放不下了：同一张卡表池子里最多 {MAX_PER_LIST} 个成员，"
                            f"已经有的和已经选了带这张卡表的队的选手加起来到上限了")
    return problems


def check_claim(sub: dict, player: str, pool, lines: list) -> tuple[list[str], dict]:
    """Problems with a 选队 submission, and what its receipt records."""
    period = pool.period
    team = sub["meta"].get("team")
    info = {"period": period, "team": team}
    if not is_special(period):
        return [f"第 {period} 期不是特殊期，不收「选队」"], info
    if style(period) != "teams":
        return [f"第 {period} 期是特殊期，但这一期不选队：直接交新卡组（{SPECIAL[period].get('guide', 'submit.md')}）"], info
    t = teams(period)
    team = info["team"] = canonical(team, t)
    if team not in t:
        return [f"没有叫 {team!r} 的队；这一期能选的是：{'、'.join(sorted(t))}（照抄这几个名字）"], info
    mine = claims(lines, period).get(player)
    if mine is not None:
        return [f"你这一期已经选了 {mine[0]}（{mine[1]}），一期只选一次，选了不能换"], info
    return room(team, player, period, pool, lines), info


def check_deck(deck_ids: list, craft: int, player: str, period: int, lines: list) -> tuple[list[str], str | None]:
    """A new deck in a special period: it must be the list of its class of the team the player picked."""
    from ladder.pool import CRAFT_ZH
    mine = claims(lines, period).get(player)
    if mine is None:
        return ["特殊期先交「选队」（submit.md、special-P3.md），选到队以后再交卡组"], None
    team = mine[0]
    entry = teams(period)[team].get(craft)                  # craft 0: all neutral, check_deck refused it already
    if entry is None:
        return [f"这一副不是你选的队 {team} 的任何一个职业的卡表；特殊期要交那一副原样（40 张一张不改）"], team
    want = entry["ids"]
    if sorted(deck_ids) != want:
        return [f"这一副不是你选的队 {team} 的{CRAFT_ZH[craft]}卡表；特殊期要交那一副原样（40 张一张不改）"], team
    return [], team


def status(lines: list, period: int, player: str) -> dict:
    """What a player's 状态.md says about the special period."""
    if style(period) == "blueprints":
        mine = accepted(lines, period).get(player, {})
        decks = [{"name": name, "craft": b["craft"], "max_changes": b["max_changes"],
                  "receipt": mine[name]["id"] if name in mine else None,
                  "changes": (mine[name].get("blueprint") or {}).get("changes") if name in mine else None}
                 for name, b in blueprints(period).items()]
        return {"special": SPECIAL[period]["title"], "special_style": "blueprints",
                "kind_zh": kind_zh(period, ""), "guide": SPECIAL[period].get("guide"), "decks": decks,
                "admits": admits(period), "takes_updates": takes_updates(period), "merged_from": first_merged()}
    t = teams(period)
    mine = claims(lines, period).get(player)
    return {"special": SPECIAL[period]["title"], "team": mine[0] if mine else None, "teams": sorted(t)}


# --- blueprints (period 4) ----------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def blueprints(period: int) -> dict:
    """{name: {"name", "craft", "max_changes", "ids" (sorted card ids), "code"}} of a blueprint period, in the order
    the spec lists them; the code is svsim's to_hash of the cards in id order."""
    from ladder import base
    from svsim.cards.decks import to_hash
    from svsim.cards.pool import card
    if style(period) != "blueprints":
        raise ValueError(f"period {period} is not a special period with blueprints")
    out = {}
    for name, b in SPECIAL[period]["blueprints"].items():
        ids = sorted(c for c, n in b["cards"].items() for _ in range(n))
        deck = [card(c) for c in ids]
        if len(ids) != 40 or int(base.craft_of(deck)) != b["craft"]:
            raise ValueError(f"the blueprint {name} has {len(ids)} cards of class {int(base.craft_of(deck))}")
        out[name] = {"name": name, "craft": b["craft"], "max_changes": b["max_changes"], "ids": ids,
                     "code": to_hash(deck)}
    if len({b["craft"] for b in out.values()}) != len(out):
        raise ValueError(f"two blueprints of one class in period {period}")
    return out


def blueprint_for(period: int, craft: int) -> dict | None:
    return next((b for b in blueprints(period).values() if b["craft"] == craft), None)


def _card_name(cid: int) -> str:
    from svsim.cards.pool import POOL
    c = POOL.get(cid)
    return (c.name_zh or c.name) if c is not None else "?"


def compare(deck_ids, blueprint_ids) -> dict:
    """How a deck differs from a blueprint, by card id: {"changes": 40 - the shared cards (as multisets), "out": the
    blueprint's cards not in the deck, "in": the deck's cards not in the blueprint}; out and in are [[id, name, n]]
    in id order."""
    from collections import Counter
    a, b = Counter(int(c) for c in deck_ids), Counter(int(c) for c in blueprint_ids)
    shared = sum((a & b).values())
    return {"changes": len(blueprint_ids) - shared,
            "out": [[c, _card_name(c), n] for c, n in sorted((b - a).items())],
            "in": [[c, _card_name(c), n] for c, n in sorted((a - b).items())]}


def _head(info: dict) -> str:
    return f"和蓝本{info['name']}比改了 {info['changes']} 张（上限 {info['max_changes']} 张）"


def describe(info: dict) -> str:
    """The change line of a receipt: 「和蓝本快攻妖精比改了 3 张（上限 7 张）：去掉 …；换上 …」."""
    head = _head(info)
    if not info["changes"] and not info["in"]:
        return head + "，和蓝本一样"
    part = lambda rows: "、".join(f"{name}（{cid}）×{n}" for cid, name, n in rows) or "没有"
    return f"{head}：去掉 {part(info['out'])}；换上 {part(info['in'])}"


def check_blueprint(deck_ids: list, craft: int, period: int) -> tuple[list[str], dict | None]:
    """A new deck in a blueprint period: the blueprint of its class with at most its max_changes cards changed. The
    receipt's record of it (name, class, changes, cap, what differs), None for a class with no blueprint."""
    names = "、".join(f"{n}（{_craft_zh(b['craft'])}）" for n, b in blueprints(period).items())
    b = blueprint_for(period, craft)
    if b is None:
        return [f"第 {period} 期是特殊期，只收这几副：{names}，各自照蓝本改；"
                f"{_craft_zh(craft) if craft else '这一副'}的新卡组这一期不收（{SPECIAL[period].get('guide')}）"], None
    info = {"name": b["name"], "craft": craft, "max_changes": b["max_changes"], **compare(deck_ids, b["ids"])}
    if info["changes"] > b["max_changes"]:      # what differs is in the receipt's 蓝本 line (precheck: its warnings)
        return [_head(info) + "，超过上限（按张数数：40 − 你这副和蓝本按卡号共有的张数；"
                              "去掉、换上了哪些见「蓝本：」那一行）"], info
    return [], info


def _craft_zh(craft) -> str:
    from ladder.pool import CRAFT_ZH
    return CRAFT_ZH.get(craft, str(craft))


def accepted(lines: list, period: int) -> dict:
    """{player: {blueprint name: receipt line}}: the accepted new decks of a blueprint period (one per class at most:
    the slot check), for the status and the period's evaluation."""
    out: dict = {}
    for l in lines:
        if (l.get("ev") == "receipt" and l.get("kind") == "deck" and l.get("verdict") == "收下"
                and l.get("period") == period and l.get("blueprint")):
            out.setdefault(l["player"], {}).setdefault(l["blueprint"]["name"], l)
    return out


def held(lines: list, player: str) -> dict:
    """{member name: receipt id}: the player's accepted new decks of a period whose decks stay out of the pool
    (period 4). Their names are taken (a name is never used twice) though no admit line holds them."""
    return {l["member"]: l["id"] for l in lines
            if l.get("ev") == "receipt" and l.get("kind") == "deck" and l.get("verdict") == "收下"
            and l.get("player") == player and is_special(l.get("period")) and not admits(l["period"])
            and l.get("member")}
