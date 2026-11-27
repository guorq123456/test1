"""Before a special period opens (A62, RUNBOOK): its round on this computer, and the room each team has in the pool as
it is now. Changes nothing: the pool is copied, the claim is received into a scratch ledger. No game, no seed.

    python analysis/ladder/tools/special_check.py --period 3 --out OUT [--host C:\\claude\\ladder-host] [--mask 0x3FC3FC]

1. the round: special.teams(P) loads (4 teams x 7 classes), the codes' checksum (sha256 of the codes joined by
   newlines, in the file's order: LD-75 has it), every list legal by submit.check_deck;
2. the pool: it must be in period P (the close before it done); for each list of the round, the active members that
   hold it (ids only: host side);
3. room: for each team, how many players could take it if they all came first (claims added one by one until
   special.room refuses), and the most claims the four teams can take together (every order of up to 5 claims,
   one per player): fewer than the five players is a problem (Salem decides);
4. a claim end to end on a copy of the pool and an empty ledger: 选队 received (收下), the same again (拒收), and the
   team's seven lists pass submit.check_slots after it.
OUT/summary.json; exit 0 if all of it holds, 1 if not.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = LADDER.parents[1]
sys.path[:0] = [str(LADDER), str(ROOT)]

from ladder.arena import PLAYERS  # noqa: E402

PLAYERS_MAX = len(PLAYERS)


def fake_claims(seq: list, period: int) -> list:
    return [{"ev": "receipt", "id": f"S-{9000 + i}", "player": f"p{i}", "period": period, "kind": "team",
             "team": t, "verdict": "收下"} for i, t in enumerate(seq)]


def most_claims(teams: list, period: int, pool) -> tuple[int, list]:
    """The most claims the teams take together, over every order of up to PLAYERS_MAX claims, and one order that
    reaches it."""
    from ladder import special
    best, how = 0, []
    for n in range(1, PLAYERS_MAX + 1):
        for seq in itertools.product(teams, repeat=n):
            ok = all(not special.room(t, f"p{i}", period, pool, fake_claims(list(seq[:i]), period))
                     for i, t in enumerate(seq))
            if ok and n > best:
                best, how = n, list(seq)
                break
    return best, how


def check(host: Path, period: int, out: Path, mask: int | None = None) -> dict:
    """`mask`: the E-cores (submit.receive compares compute, A44: on Windows it refuses to start without one)."""
    from ladder import special, submit
    from ladder.pool import CRAFT_ZH, Pool, list_key
    res = {"period": period, "ok": False, "problems": []}
    if not special.is_special(period):
        res["problems"].append(f"period {period} is not special")
        return res
    t = special.teams(period)
    src = LADDER / special.SPECIAL[period]["decklists"]
    codes = [l.split("|")[1] for l in src.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    res["round"] = {"file": special.SPECIAL[period]["decklists"], "teams": {k: len(v) for k, v in t.items()},
                    "codes": len(codes), "codes_sha256": hashlib.sha256("\n".join(codes).encode()).hexdigest()[:16]}
    illegal = {f"{team} {CRAFT_ZH[c]}": p for team, by in t.items() for c, e in by.items()
               if (p := submit.check_deck(e["code"])[1])}
    res["round"]["illegal"] = illegal
    if illegal:
        res["problems"].append(f"{len(illegal)} lists not legal")
    pool = Pool(host / "pool")
    res["pool_period"] = pool.period
    if pool.period != period:
        res["problems"].append(f"the pool is in period {pool.period}, not {period}: close period {period - 1} first")
        return res
    held = {}
    for team, by in sorted(t.items()):
        for c, e in sorted(by.items()):
            mids = [m.mid for m in pool.active() if list_key(m.deck) == list_key(e["ids"])]
            if mids:
                held[f"{team} {CRAFT_ZH[c]}"] = mids
    res["held"] = held
    alone = {}
    for team in sorted(t):
        seq = []
        while len(seq) < PLAYERS_MAX and not special.room(team, f"p{len(seq)}", period, pool,
                                                          fake_claims(seq, period)):
            seq.append(team)
        alone[team] = len(seq)
    res["room_alone"] = alone
    res["room_together"], res["room_order"] = most_claims(sorted(t), period, pool)
    res["enough"] = res["room_together"] >= PLAYERS_MAX
    if not res["enough"]:
        res["problems"].append(f"only {res['room_together']} of the {PLAYERS_MAX} players can get a team")
    # 4: a claim end to end, on a copy (a stop in it is a problem written down, with 1-3 kept: before-P3, 11-24)
    try:
        _claim(host, period, out, mask, t, alone, res)
    except (Exception, SystemExit) as e:                    # noqa: BLE001
        res["problems"].append(f"the claim end to end stopped: {type(e).__name__}: {e}")
    res["ok"] = not res["problems"]
    return res


def _claim(host: Path, period: int, out: Path, mask, t: dict, alone: dict, res: dict):
    from ladder import submit
    from ladder.pool import CRAFT_ZH, Pool
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        tmp = Path(tmp)
        shutil.copytree(host / "pool", tmp / "pool")
        team = next((k for k in sorted(t) if alone[k] > 0), None)
        if team is None:
            res["problems"].append("no team has room")
            return
        d = tmp / "in" / "选队"
        d.mkdir(parents=True)
        (d / "submission.json").write_text(json.dumps({"type": "选队", "team": team}, ensure_ascii=False),
                                           encoding="utf-8")
        first = submit.receive(d, "astra", tmp / "pool", tmp / "subs", mask=mask)
        again = submit.receive(d, "astra", tmp / "pool", tmp / "subs", mask=mask)
        lines = submit.ledger(tmp / "subs")
        slots = {}
        for c, e in sorted(t[team].items()):
            sub = {"kind": "deck", "meta": {"member": f"dry-{c}"}, "deck_ids": submit.check_deck(e["code"])[0]}
            slots[CRAFT_ZH[c]] = submit.check_slots(sub, "astra", Pool(tmp / "pool"), lines)[0]
        st = submit.status(tmp / "subs", tmp / "pool", "astra")
        res["claim"] = {"team": team, "first": first["verdict"], "again": again["verdict"],
                        "again_reasons": again["reasons"], "slots": slots, "status_team": st.get("team")}
        if first["verdict"] != "收下" or again["verdict"] != "拒收" or any(slots.values()) or st.get("team") != team:
            res["problems"].append("the claim end to end did not go as it should")


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", type=int, required=True)
    ap.add_argument("--host", type=Path, default=Path(r"C:\claude\ladder-host"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mask", default="0x3FC3FC", help="the E-cores (receiving compares compute, A44); 'none' off Windows")
    a = ap.parse_args(argv)
    mask = None if a.mask == "none" else int(a.mask, 16)
    a.out.mkdir(parents=True, exist_ok=True)
    from ladder import special
    if special.style(a.period) != "teams":                 # period 4 (three blueprints, no claim): nothing to check
        res = {"period": a.period, "ok": False, "problems": [
            f"第 {a.period} 期不是按队选的特殊期：这个检查只给第 3 期那种「选队」的特殊期用"
            + ("（第 4 期是三副蓝本，不选队，开期前不用跑它）" if special.style(a.period) == "blueprints" else "")]}
    else:
        try:
            res = check(a.host, a.period, a.out, mask)
        except (Exception, SystemExit) as e:                # written down, not lost in a closed window
            res = {"period": a.period, "ok": False, "problems": [f"{type(e).__name__}: {e}"]}
    (a.out / "summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
