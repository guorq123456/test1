"""Salem's lab (S30): his own practice interface, all cores, no cap, everything visible. Seeds: the host's second
probe bank, 93409090-93409139 (SEEDS.md; every run of these tests plays them again)."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
from ladder import arena, lab  # noqa: E402
from ladder.pool import Pool  # noqa: E402

ROOT = HERE.parents[2]
LINES = [l.strip().split("|") for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(encoding="utf-8")
         .splitlines() if l.strip() and not l.startswith("#")]
LABELS = [n for n, _ in LINES]
CODES = [c for _, c in LINES]
FAST = "bot:mcts:8"
QUICK = '''
from ladder.interface import PlayerStrategy


class Quick(PlayerStrategy):
    LETHAL = "exact"

    def search(self, pos):
        return {"iterations": 8}
'''


def version(d: Path, src: str, deck: str) -> Path:
    d.mkdir(parents=True)
    (d / "strategy.py").write_text(src, encoding="utf-8")
    (d / "submission.json").write_text(json.dumps({"class": "Quick", "deck": deck}), encoding="utf-8")
    return d


@pytest.fixture()
def L(tmp_path, monkeypatch):
    monkeypatch.setattr(lab, "LAB_SEEDS", (93409090, 93409140))
    from ladder.runner import load_deck
    pool = Pool.create(tmp_path / "pool", seeds=(93400190, 93400200), rng_seed=3, check=True)
    for code, cr in ((CODES[1], 1450), (CODES[2], 1500)):
        pool.enter([c.card_id for c in load_deck(code)], FAST, "baseline", cr=cr)
    pool.enter([c.card_id for c in load_deck(CODES[4])], FAST, "fable", cr=1550)
    anchors = tmp_path / "anchors.json"
    anchors.write_text(json.dumps([{"name": "bot 贪心", "deck": CODES[5], "strategy": "bot:greedy"}],
                                  ensure_ascii=False), encoding="utf-8")
    a = tmp_path / "arena"
    arena.snapshot(tmp_path / "pool", a, anchors, cr="current")
    return lab.Lab(tmp_path / "lab", a, workers=2)


def test_the_field_shows_everything(L):
    f = L.field_rows()
    rows = {r.get("mid", r["id"]): r for r in f["opponents"]}
    assert rows["m0003"]["owner"] == "fable" and rows["m0003"]["strategy"] == FAST
    assert rows["m0003"]["deck"] == LABELS[4] and rows["m0003"]["rel_cr"] == 50
    assert f["window_open"] is False and (L.dir / "lab.key").exists()


def test_vs_in_turns_under_the_arena_lock(L, monkeypatch):
    monkeypatch.setattr(arena, "RUN_GAMES_MAX", 2)            # turns of 2 games: 5 games are three turns
    me = L.mine(None, LABELS[6], FAST)
    anon = next(m["anon"] for m in L.field["members"] if m["mid"] == "m0003")
    out = L.vs(me, L.opponents([anon, "m0001"], None, None, None), 5, rng_seed=1)
    assert out["games"] == 5 and out["decided"] + out["void"] <= 5
    assert set(out["by_opponent"]) == {anon, L.by_id["m0001"][1]["anon"]}
    assert out["first"]["games"] + out["second"]["games"] == out["decided"]
    lines = [json.loads(x) for x in (L.dir / "runs" / out["run"] / "games.jsonl").read_text(encoding="utf-8")
             .splitlines()]
    assert len(lines) == 5 and all(93409090 <= g["seed"] < 93409140 for g in lines)
    served = json.loads((L.arena / "host" / "served.json").read_text(encoding="utf-8"))
    assert "salem" in served and list((L.arena / "host" / "queue").glob("*.t")) == []


def test_a_version_against_archive_decks_and_the_same_games_again(L, tmp_path):
    v = version(tmp_path / "v1", QUICK, LABELS[6])                   # a label of the archive as the deck
    me = L.mine(str(v), None, None)
    assert me["spec"].startswith("py:lab_") and me["label"] == LABELS[6] and me["warnings"] == []
    opps = L.opponents(None, None, [LABELS[0], CODES[3]], FAST)
    first = L.vs(me, opps, 4, rng_seed=2)
    again = L.vs(L.mine(None, LABELS[6], FAST), None, 0, same_as=first["run"])
    assert again["games"] == 4 and again["paired"] is not None and again["paired"]["games"] <= 4
    jobs = [json.loads(x) for x in (L.dir / "runs" / first["run"] / "games.jsonl").read_text(encoding="utf-8")
            .splitlines()]
    jobs2 = [json.loads(x) for x in (L.dir / "runs" / again["run"] / "games.jsonl").read_text(encoding="utf-8")
             .splitlines()]
    assert sorted(g["seed"] for g in jobs) == sorted(g["seed"] for g in jobs2)
    p = L.replay(first["run"], jobs[0]["id"], seat=0)
    body = json.loads(p.read_text(encoding="utf-8"))
    assert body["moves"] and body["views"] and body["view_seat"] == 0


def test_refusals(L, tmp_path):
    with pytest.raises(lab.LabError):
        L.mine(None, None, None)
    with pytest.raises(lab.LabError, match="模拟器不收|不认识"):
        L.mine(None, "no-such-deck", None)
    me = L.mine(None, LABELS[6], FAST)
    with pytest.raises(lab.LabError, match="没有"):
        L.opponents(["zzzzzz"], None, None, None)
    assert [o["key"] for o in L.opponents(None, "Abyss", None, None)] == ["m0003"]   # bot/T1-ABYSS-1
    assert L.opponents(None, "梦魇", None, None) == L.opponents(None, "abyss", None, None)
    with pytest.raises(lab.LabError, match="没有这个职业"):
        L.opponents(None, "elf", None, None)
    with pytest.raises(lab.LabError, match="给一种"):
        L.opponents(["m0001"], "精灵", None, None)
    with pytest.raises(lab.LabError, match="训练模型"):
        L.check_trained([["bot:pilot-T1-SWORD-1", "py:lab_x:Quick"]])
    L.check_trained([["bot:pilot-T1-SWORD-1", FAST]])                # host against host is fine
    with pytest.raises(lab.LabError, match="训练模型"):
        L.ladder(dict(me, spec="bot:pilot-T1-SWORD-1"), None, 4, 2, 2)
    assert not (L.dir / "runs").exists() or list((L.dir / "runs").iterdir()) == []


def test_ladder_capped_only_while_a_window_is_open(L, monkeypatch):
    me = L.mine(None, LABELS[6], FAST)
    arena.open_window(L.arena, hours=1, games=60, workers=2)
    L2 = lab.Lab(L.dir, L.arena, workers=2)
    monkeypatch.setattr(lab, "LADDER_OPEN_MAX", 10)
    with pytest.raises(lab.LabError, match="期中"):
        L2.ladder(me, None, 4, 2, 2)                                 # 8 games + 30 for voids > 10
    (L.arena / "public" / "window.json").unlink()                     # between periods: no cap
    out = L2.ladder(me, "m0001", 4, 2, 2)
    assert out["kind"] == "ladder" and ("rel_cr" in out or "stopped" in out)
