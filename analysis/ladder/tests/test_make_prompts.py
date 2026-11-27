"""tools/make_prompts.py: the five players' prompts, the name filled in, no host comment or placeholder left, LF on
every machine (a Windows checkout of the source is CRLF), each file's hash the one printed."""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

import make_prompts as M  # noqa: E402

SRC = HERE.parent / "player-prompt-v2.md"


def test_five_prompts_lf_and_their_hashes(tmp_path):
    crlf = tmp_path / "p.md"
    crlf.write_bytes(SRC.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    a, b = M.make(crlf, tmp_path / "a"), M.make(SRC, tmp_path / "b")
    assert a == b and list(a) == ["fable-ultracode", "fable", "astra", "opus", "sol"]
    for name, h in a.items():
        data = (tmp_path / "a" / f"{name}.md").read_bytes()
        assert b"\r\n" not in data and b"{{" not in data and b"<!--" not in data
        assert hashlib.sha256(data).hexdigest()[:12] == h
        assert f"选手名 {name}".encode("utf-8") in data
        others = [n for n in a if n != name and n not in name and name not in n]
        assert not any(f"players\\{o}\\".encode("utf-8") in data for o in others)


def test_a_period_note_goes_in_front_of_the_periods_section(tmp_path):
    note = HERE.parent / "prompt-note-P3.md"
    got = M.make(SRC, tmp_path / "n", note)
    plain = M.make(SRC, tmp_path / "p")
    assert set(got) == set(plain) and all(got[k] != plain[k] for k in got)
    text = (tmp_path / "n" / "sol.md").read_text(encoding="utf-8")
    head = note.read_text(encoding="utf-8").strip().splitlines()[0]
    assert text.count(head) == 1 and text.index(head) < text.index("## 每一期怎么过") < text.index("## 提交格式")


def test_period_4s_note_and_the_prompt_agree(tmp_path):
    # Salem 11-27: period 4 is special (three blueprints, no updates, decks kept out of the pool), merged from 5
    note = HERE.parent / "prompt-note-P4.md"
    M.make(SRC, tmp_path / "p4", note)
    text = (tmp_path / "p4" / "astra.md").read_text(encoding="utf-8")
    assert text.count("## 这一期（第 4 期）是特殊期") == 1
    assert text.index("## 这一期（第 4 期）是特殊期") < text.index("## 每一期怎么过")
    assert "第 4 期起每一期都是合并期" not in text and "**第 5 期起每一期都是合并期" in text
    assert "special-P4.md" in text and "快攻妖精、跳费龙最多改 7 张，兔子教最多改 6 张" in text
    assert "precheck 你的提交目录 --period 4" in text and "合并期从第 5 期起" in text


def test_help_is_not_taken_for_the_output_folder(tmp_path):
    import subprocess
    tool = HERE.parent / "tools" / "make_prompts.py"
    for args, code in ((["--help"], 0), (["-h"], 0), ([], 2), (["--note", "x.md"], 2)):
        r = subprocess.run([sys.executable, str(tool), *args], cwd=tmp_path, capture_output=True, text=True,
                           encoding="utf-8", check=False)
        assert r.returncode == code and "OUTDIR" in r.stdout, (args, r.stderr)
    assert list(tmp_path.iterdir()) == []                               # no "--help" folder, nothing written
