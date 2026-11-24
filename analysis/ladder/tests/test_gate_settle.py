"""tools/gate_settle.py (S31): period-2 updates whose gate stopped with the old tool's p_of_gap error are recorded as
not passed without new games. Made-up ledgers; no game is played and no seed is used (the pool's range is
test_collect's, nothing is drawn from it)."""
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[2]), str(HERE.parent / "tools"), str(HERE)]

import gate_settle as S  # noqa: E402
from ladder import gate as G  # noqa: E402
from ladder.pool import Pool  # noqa: E402
from test_pool import BASE_DECKS  # noqa: E402

ERR = "ValueError: a gap of 5.0 pp can't happen with a discordant share of {}"


def _w(p: Path, rec):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _games(d: Path, gid: str, discordant: int, pairs: int = 200):
    """An attempt's share pre-run: `discordant` pairs the new version won, the rest the same."""
    d.mkdir(parents=True, exist_ok=True)
    with (d / "games.jsonl").open("w", encoding="utf-8") as f:
        for i in range(pairs):
            seat = i % 2
            for side in ("new", "old"):
                won = side == "new" or i >= discordant
                f.write(json.dumps({"id": f"{gid}-pre{i:05d}-{side}", "seed": 1000 + i, "result": "normal",
                                    "winner": seat if won else 1 - seat,
                                    "labels": {"gate": gid, "pair": i, "side": side, "member_seat": seat}}) + "\n")


def _start(d: Path, gid, m, new, old, change="改了换手", prediction="+5 pp"):
    d.mkdir(parents=True, exist_ok=True)
    (d / "start.json").write_text(json.dumps({"gate": gid, "member": m.mid, "anon": m.anon, "kind": "better",
                                              "new": new, "old": old, "change": change, "prediction": prediction},
                                             ensure_ascii=False), encoding="utf-8")


def _host(tmp_path, share_a="0.05", discordant_a=4):
    """Three members A, B, C. G-0001: B's update passed (share 0.04). S-0002 (A): stopped after its 200 pre pairs
    (G-0002, named by the next gate). S-0003 (B): stopped with no game (the share was G-0001's), in G-0003's folder.
    S-0004 (C): reused that folder, played its pre pairs, stopped; the last one, not named yet."""
    host = tmp_path / "host"
    pool = Pool.create(host / "pool", seeds=(99001460, 99001470), rng_seed=1)
    pool.advance(force="test")                                                 # period 1: a deck period
    ma, mb, mc = (pool.members[pool.enter(BASE_DECKS[c], "py:helpers:Random", "fable", rng=random.Random(c))]
                  for c in (0, 4, 6))
    pool.advance(force="test")                                                 # period 2: a strategy period
    subs, gates = host / "subs", host / "gates"
    gates.mkdir(parents=True)
    (gates / "delta-P2.json").write_text('{"delta": 5}', encoding="utf-8")
    for rid, m, who in (("S-0001", mb, "fable"), ("S-0002", ma, "fable"), ("S-0003", mb, "fable"),
                        ("S-0004", mc, "astra")):
        mod = "sub_" + rid.replace("-", "")
        _w(subs / "submissions.jsonl", {"ev": "receipt", "id": rid, "player": who, "period": 2, "kind": "update",
                                        "verdict": "收下", "member": f"成员{m.craft}", "mid": m.mid,
                                        "spec": f"py:{mod}:Mine", "dir": f"d{rid}"})
        (subs / "code").mkdir(parents=True, exist_ok=True)
        (subs / "code" / f"{mod}.py").write_text(f"class Mine:\n    '''{rid}'''\n    x = {rid[-1]}\n", encoding="utf-8")
        (subs / rid).mkdir(parents=True)
        (subs / rid / "receipt.md").write_text(f"# 回执 {rid}：收下\n", encoding="utf-8")
        (subs / rid / "submission.json").write_text(json.dumps({"change": "改了换手", "prediction": "+5 pp"},
                                                               ensure_ascii=False), encoding="utf-8")
    base = {"date": "11-24", "kind": "better", "change": "改了换手", "prediction": "+5 pp", "seed_note": "—",
            "opponents_note": "—"}
    G.append_ledger(dict(base, gate="G-0001", member=mb.mid, anon=mb.anon, new="py:sub_S0001:Mine",
                         old="py:helpers:Random", verdict="passed", discordant_share=0.04, seeds_used=[1]), gates)
    pool.update(mb.mid, "py:sub_S0001:Mine", gate="G-0001")
    _w(subs / "submissions.jsonl", {"ev": "gated", "receipt": "S-0001", "player": "fable", "mid": mb.mid,
                                    "gate": "G-0001", "verdict": "passed", "old": "py:helpers:Random",
                                    "new": "py:sub_S0001:Mine", "time": "2026-11-24T20:06:00+00:00"})
    _start(gates / "G-0002", "G-0002", ma, "py:sub_S0002:Mine", "py:helpers:Random")
    _games(gates / "G-0002", "G-0002", discordant_a)
    _w(subs / "collect.jsonl", {"ev": "gate-failed", "receipt": "S-0002", "error": ERR.format(share_a),
                                "time": "2026-11-24T20:10:00+00:00"})
    G.record_interrupted(gates, G.read_ledger(gates), gates)                  # what S-0003's gate did first
    _start(gates / "G-0003", "G-0003", mb, "py:sub_S0003:Mine", "py:sub_S0001:Mine")
    _w(subs / "collect.jsonl", {"ev": "gate-failed", "receipt": "S-0003", "error": ERR.format("0.04"),
                                "time": "2026-11-24T20:12:00+00:00"})
    _start(gates / "G-0003", "G-0003", mc, "py:sub_S0004:Mine", "py:helpers:Random")   # the same folder again
    _games(gates / "G-0003", "G-0003", 9)
    _w(subs / "collect.jsonl", {"ev": "gate-failed", "receipt": "S-0004", "error": ERR.format("0.05"),
                                "time": "2026-11-24T20:15:00+00:00"})
    with (subs / "collect.jsonl").open("a", encoding="utf-8") as f:
        f.write('{"ev": "gate-fai\x00\x00')                               # a power cut's torn line (LD-42)
    return host, (ma, mb, mc)


def test_three_stopped_gates_are_settled_not_passed(tmp_path):
    host, (ma, mb, mc) = _host(tmp_path)
    players, gates, subs = tmp_path / "players", host / "gates", host / "subs"
    before = {p: p.read_bytes() for p in (gates / "gates.jsonl", gates / "GATES.md", subs / "submissions.jsonl")}
    dry = S.settle(host, players, ["S-0002", "S-0003", "S-0004"], write=False)
    assert dry["problems"] == [] and not dry["written"] and dry["named_stopped"] == ["G-0003"]
    assert [x["gate_line"]["gate"] for x in dry["settle"]] == ["G-0004", "G-0005", "G-0006"]
    assert {p: p.read_bytes() for p in before} == before and not players.exists()    # the dry run wrote nothing

    res = S.settle(host, players, ["S-0002", "S-0003", "S-0004"], write=True)
    assert res["problems"] == [] and res["written"] and res["named_stopped"] == ["G-0003"]
    gl = G.read_ledger(gates)
    assert [(r["gate"], r["verdict"][:11]) for r in gl] == [
        ("G-0001", "passed"), ("G-0002", "interrupted"), ("G-0003", "interrupted"),
        ("G-0004", "not passed"), ("G-0005", "not passed"), ("G-0006", "not passed")]
    s4, s5, s6 = gl[3:]
    assert (s4["settles"], s5["settles"], s6["settles"]) == ("G-0002", None, "G-0003")
    assert s4["member"] == ma.mid and s4["new"] == "py:sub_S0002:Mine" and s4["old"] == "py:helpers:Random"
    assert s4["share_source"] == {"measured_on": 200, "discordant": 4} and s4["share_seen"] == 0.05
    assert s5["old"] == "py:sub_S0001:Mine" and s5["share_source"] == {"from_ledger": ["G-0001"]}
    assert s6["share_source"] == {"measured_on": 200, "discordant": 9} and s6["share_seen"] == 0.05
    assert not any("discordant_share" in r for r in gl[3:])      # a later gate of A or C measures its share again
    assert all(r["pairs"] == 0 and r["seeds_used"] == [] and "S31" in r["estimate_note"] for r in gl[3:])
    assert "补记（S31）" in (gates / "GATES.md").read_text(encoding="utf-8")
    gated = [l for l in map(json.loads, (subs / "submissions.jsonl").read_text(encoding="utf-8").splitlines())
             if l.get("ev") == "gated" and l.get("settled")]
    assert [(l["receipt"], l["gate"], l["verdict"], l["old"]) for l in gated] == [
        ("S-0002", "G-0004", "not passed", "py:helpers:Random"), ("S-0003", "G-0005", "not passed", "py:sub_S0001:Mine"),
        ("S-0004", "G-0006", "not passed", "py:helpers:Random")]
    # the player sees the result, not the gate, its opponents or seeds; astra gets only theirs
    note = (players / "fable" / "receipts" / "dS-0002-检验.md").read_text(encoding="utf-8")
    assert "检验没过" in note and "resubmit_of（S-0002）" in note and "G-0" not in note
    assert (players / "astra" / "receipts" / "dS-0004-检验.md").exists()
    assert not (players / "astra" / "receipts" / "dS-0002-检验.md").exists()
    # the next gate takes the next number; a second run settles nothing
    assert f"G-{len(G.read_ledger(gates)) + 1:04d}" == "G-0007"
    again = S.settle(host, players, ["S-0002"], write=True)
    assert not again["written"] and "已经有检验结果" in again["problems"][0]


def test_a_share_that_does_not_match_its_games_is_refused(tmp_path):
    host, _ = _host(tmp_path, discordant_a=16)                     # 16 of 200: 0.08, the error said 0.05
    res = S.settle(host, tmp_path / "players", ["S-0002", "S-0003"], write=True)
    assert not res["written"] and any("0.0800" in p for p in res["problems"])
    assert not any(l.get("ev") == "gated" and l.get("settled") for l in map(
        json.loads, (host / "subs" / "submissions.jsonl").read_text(encoding="utf-8").splitlines()))


def test_a_receipt_without_that_error_is_refused(tmp_path):
    host, _ = _host(tmp_path)
    res = S.settle(host, tmp_path / "players", ["S-0001", "S-0009"], write=False)
    assert len(res["problems"]) == 2 and res["settle"] == []
