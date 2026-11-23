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
