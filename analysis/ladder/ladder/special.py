"""Special periods (Salem's S27, 11-24 14:22Z and 14:47Z): a deck period in which each player picks one team of a pro
league round and hands in that team's seven decks, one per class, not one card changed, with strategies of their own.
Period 3: Premier Series 26-27 round 11, second half (11/18 JST): four teams, 28 lists (decklists/ps11b-2026-11-18.txt).

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

Nothing here changes the pool (pool.py is locked): the claims live in the submissions ledger, the decks enter through
submit.admit like any deck period's.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

LADDER = Path(__file__).resolve().parents[1]

SPECIAL = {
    3: {"decklists": "decklists/ps11b-2026-11-18.txt",
        "title": "职业联赛 Premier Series 26-27 第 11 节后半（11/18）"},
}
MAX_PLAYERS_PER_TEAM = 2


def is_special(period: int) -> bool:
    return period in SPECIAL


@lru_cache(maxsize=None)
def teams(period: int) -> dict:
    """{team: {craft: {"label", "code", "ids" (sorted card ids), "player"}}} of a special period's round."""
    from ladder import base
    from ladder.runner import load_deck
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
    t = teams(period)
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
    want = teams(period)[team][craft]["ids"]
    if sorted(deck_ids) != want:
        return [f"这一副不是你选的队 {team} 的{CRAFT_ZH[craft]}卡表；特殊期要交那一副原样（40 张一张不改）"], team
    return [], team


def status(lines: list, period: int, player: str) -> dict:
    """What a player's 状态.md says about the special period."""
    t = teams(period)
    mine = claims(lines, period).get(player)
    return {"special": SPECIAL[period]["title"], "team": mine[0] if mine else None, "teams": sorted(t)}
