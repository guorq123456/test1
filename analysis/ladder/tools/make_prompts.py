"""The five players' prompts from player-prompt-v2.md (S20: one per player, the name filled in).

    python analysis/ladder/tools/make_prompts.py OUTDIR [--note NOTE.md]

Drops the first line (the host's comment, `<!-- ... -->`) and the blank lines after it, puts each player's name
(ladder.arena.PLAYERS) for {{名字}}, and stops if any `{{` or `<!--` is left. Writes OUTDIR/<name>.md (UTF-8) and
prints each file's sha256 (first 12). `--note`: a period's own section (prompt-note-P3.md, the special period S27;
prompt-note-P4.md, special period 4's three blueprints, Salem 11-27) put in front of 「## 每一期怎么过」, the same for
every player. Nothing else here depends on the period: the prompt itself says period 4 is special and merged periods
start at 5."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
sys.path[:0] = [str(LADDER), str(LADDER.parents[1])]


EXTRA = {   # one player's own conditions, at the end of their prompt (Salem's word; nothing about the others)
    "fable-ultracode": "\n## 你这位选手的附加条件\n\n"
                       "* 你派出的子代理、工作流里的子任务一律用 Opus 或 Sonnet 模型（Agent 工具的 model 填 opus 或 sonnet；"
                       "Workflow 脚本里 agent() 的选项写 model: 'opus' 或 'sonnet'）。你自己这个主会话不变。"
                       "这一条从第 1 期中途起一直有效，原因是额度，和你的表现无关。\n",   # S24, Salem 11-24 09:05Z
}


ANCHOR = "\n## 每一期怎么过\n"


def make(src: Path, out: Path, note: Path | None = None) -> dict:
    from ladder.arena import PLAYERS
    text = src.read_bytes().decode("utf-8").replace("\r\n", "\n")      # a Windows checkout is CRLF
    first, _, rest = text.partition("\n")
    if not (first.startswith("<!--") and first.rstrip().endswith("-->")):
        raise SystemExit("the first line is not the host's comment")
    rest = rest.lstrip("\n")
    if note is not None:
        add = note.read_bytes().decode("utf-8").replace("\r\n", "\n").strip("\n")
        if rest.count(ANCHOR) != 1:
            raise SystemExit("the prompt has no single 「## 每一期怎么过」 to put the note in front of")
        rest = rest.replace(ANCHOR, "\n" + add + "\n" + ANCHOR)
    out.mkdir(parents=True, exist_ok=True)
    got = {}
    for name in PLAYERS:
        body = rest.replace("{{名字}}", name)
        if name in EXTRA:
            body = body.rstrip("\n") + "\n" + EXTRA[name]
        if "{{" in body or "}}" in body or "<!--" in body:
            raise SystemExit(f"{name}: a placeholder or a host comment is left")
        (out / f"{name}.md").write_bytes(body.encode("utf-8"))     # LF on every machine: the hash is the file's
        got[name] = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
    return got


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):     # --help (or nothing): never taken for OUTDIR
        print(__doc__)
        sys.exit(0 if sys.argv[1:2] in (["-h"], ["--help"]) else 2)
    src = LADDER / "player-prompt-v2.md"
    out = Path(sys.argv[1])
    note = Path(sys.argv[sys.argv.index("--note") + 1]) if "--note" in sys.argv else None
    got = make(src, out, note)
    lines = ["# 五份成品提示词", "",
             f"从 analysis/ladder/player-prompt-v2.md 生成（那份的 sha256 前 12 位 "
             f"{hashlib.sha256(src.read_bytes().replace(b'\r\n', b'\n')).hexdigest()[:12]}，按 LF 算）。每个选手的会话第一条消息贴自己那份的全文。"
             + (f"「每一期怎么过」前面加了这一期的一节：{note.name}（sha256 前 12 位 "
                f"{hashlib.sha256(note.read_bytes().replace(b'\r\n', b'\n')).hexdigest()[:12]}）。" if note else "")
             + "".join(f"{k} 那份末尾多一节附加条件（tools/make_prompts.py 的 EXTRA）。" for k in EXTRA), "",
             "| 选手 | 文件 | sha256 前 12 位 |", "|---|---|---|"]
    lines += [f"| {k} | {k}.md | {v} |" for k, v in got.items()]
    (out / "PROMPTS.md").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    for k, v in got.items():
        print(k, v)
