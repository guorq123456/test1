"""The turn-start budget's K as the players' documents state it (11-28, the review of the turn-start hook): K is
defined once, submit.TURN_K (pending Salem's decision card, 11-27: 1, 2 or 4); every "K is now N" in the documents
and every number worked out from K must follow it, so changing TURN_K without the documents fails here."""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
from ladder.submit import COMPUTE_CAP, COMPUTE_REFUSE, TURN_K, TURN_REFUSE  # noqa: E402

LADDER = HERE.parent
NOW = (r"K 现在是 (\d+)", r"现在 K = (\d+)", r"\| (\d+)（现在） \|")
WHERE = {                     # each document that states the current K, with how many times at least
    "public/base-interface.md": 3, "public/rules.md": 1, "public/submit.md": 1, "public/special-P4.md": 1,
    "prompt-note-P4.md": 1}


def _read(name):
    return (LADDER / name).read_text(encoding="utf-8")


def _times(x: float) -> str:
    return f"{x:g}"


def test_every_stated_k_is_submit_turn_k():
    for name, least in WHERE.items():
        text = _read(name)
        got = [int(n) for pat in NOW for n in re.findall(pat, text)]
        assert len(got) >= least, (name, got)
        assert set(got) == {TURN_K}, (name, got, TURN_K)
    for p in sorted((LADDER / "public").glob("*.md")):
        if f"public/{p.name}" not in WHERE:
            assert not any(re.search(pat, p.read_text(encoding="utf-8")) for pat in NOW), p.name


def test_numbers_worked_out_from_k_follow_it():
    # a planner that spends its whole budget: each own turn about 1 + K default turns, a game against the default
    # about (1 + K + 1) / 2 times the default's
    arena = _read("public/arena.md")
    m = re.findall(r"K = (\d+) 时，预算用满的打法每个自己回合大约花默认打法的 ([\d.]+) 倍，对默认打法的一局大约要 ([\d.]+) 倍的时间",
                   arena)
    assert m, "arena.md's worked-out times"
    for k, turn, game in m:
        assert int(k) == TURN_K and turn == _times(1 + TURN_K) and game == _times((2 + TURN_K) / 2), m
    special = _read("public/special-P4.md")
    m = re.findall(r"K = (\d+) 用满时，对默认打法的一局大约要 ([\d.]+) 倍的时间", special)
    assert m, "special-P4.md's worked-out time"
    for k, game in m:
        assert int(k) == TURN_K and game == _times((2 + TURN_K) / 2), m
    stray = [x for name in WHERE for x in re.findall(r"K = (\d+) (?:时|用满时)", _read(name))]
    assert set(stray) <= {"0", str(TURN_K)}, stray        # K = 0: the switch that turns the turn rule off


def test_the_conversion_table_is_arithmetic_on_k():
    # base-interface.md's table: K x 79.8 ms (the default's own turn, LD-95's PC run) over the medians it names
    doc = _read("public/base-interface.md")
    rows = re.findall(r"^\| (\d+)(?:（现在）)? \| (\d+) 毫秒 \| 约 ([\d.]+) 套 \| 约 (\d+) 次 \| 约 (\d+) 次 \|$", doc, re.MULTILINE)
    assert [int(r[0]) for r in rows] == [1, 2, 4], rows
    assert TURN_K in [int(r[0]) for r in rows]
    for k, ms, sets, two, opp in rows:
        give = 79.8 * int(k)
        assert int(ms) == round(give, -1) and float(sets) == round(give / 48.6, 1), (k, ms, sets)
        assert int(two) == round(give / 3.7) and int(opp) == round(give / 1.3), (k, two, opp)


def test_the_refusal_lines_in_the_documents():
    assert TURN_REFUSE == round(COMPUTE_REFUSE / COMPUTE_CAP, 3) == 1.065
    for name in ("public/base-interface.md", "public/rules.md", "public/special-P4.md"):
        assert "1.065" in _read(name), name
