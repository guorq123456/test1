"""The five players' prompts from player-prompt-v2.md (S20: one per player, the name filled in).

    python analysis/ladder/tools/make_prompts.py OUTDIR

Drops the first line (the host's comment, `<!-- ... -->`) and the blank lines after it, puts each player's name
(ladder.arena.PLAYERS) for {{名字}}, and stops if any `{{` or `<!--` is left. Writes OUTDIR/<name>.md (UTF-8) and
prints each file's sha256 (first 12)."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
sys.path[:0] = [str(LADDER), str(LADDER.parents[1])]


def make(src: Path, out: Path) -> dict:
    from ladder.arena import PLAYERS
    text = src.read_bytes().decode("utf-8").replace("\r\n", "\n")      # a Windows checkout is CRLF
    first, _, rest = text.partition("\n")
    if not (first.startswith("<!--") and first.rstrip().endswith("-->")):
        raise SystemExit("the first line is not the host's comment")
    rest = rest.lstrip("\n")
    out.mkdir(parents=True, exist_ok=True)
    got = {}
    for name in PLAYERS:
        body = rest.replace("{{名字}}", name)
        if "{{" in body or "}}" in body or "<!--" in body:
            raise SystemExit(f"{name}: a placeholder or a host comment is left")
        (out / f"{name}.md").write_bytes(body.encode("utf-8"))     # LF on every machine: the hash is the file's
        got[name] = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
    return got


if __name__ == "__main__":
    src = LADDER / "player-prompt-v2.md"
    out = Path(sys.argv[1])
    got = make(src, out)
    lines = ["# 五份成品提示词", "",
             f"从 analysis/ladder/player-prompt-v2.md 生成（那份的 sha256 前 12 位 "
             f"{hashlib.sha256(src.read_bytes().replace(b'\r\n', b'\n')).hexdigest()[:12]}，按 LF 算）。每个选手的会话第一条消息贴自己那份的全文。", "",
             "| 选手 | 文件 | sha256 前 12 位 |", "|---|---|---|"]
    lines += [f"| {k} | {k}.md | {v} |" for k, v in got.items()]
    (out / "PROMPTS.md").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    for k, v in got.items():
        print(k, v)
