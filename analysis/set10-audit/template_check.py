"""Does the official text make a sentence after an "if" clause conditional? A survey of the official card data in every
language present under data/raw/ (set_<id>_<lang>.json from svsim.tools.fetch_cards; Cygames' data, never committed).

Question (2026-10-31): Obliviationist Mugger (11043110) and Collection Manifest (11042310). The JA text puts the
second effect in its own sentence after 「…なら、…。」; the EN text joins it to the condition with "and". Which reading
does the official text support?

What it prints (counts and short card names only, no card text except for the two cards in question):
  1. the two cards' ability text in every language present;
  2. JA convention: ability blocks with a 「なら、」 sentence followed by another sentence in the same block
     ("split"), and blocks where the 「なら、」 sentence goes on with a second clause after a comma ("joined");
  3. for the "split" blocks, whether the EN block of the same card has the same number of sentences (EN also splits:
     the second effect reads unconditional) or one fewer (EN merged it into the condition, as for the Mugger);
     the same for CHS/CHT/KO when present;
  4. up to 40 card ids and EN names of the "JA split, EN merged" kind, to look them up by hand.

    python analysis/set10-audit/template_check.py [data/raw]
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAW = Path(sys.argv[1] if len(sys.argv) > 1 else "data/raw")
TARGETS = (11043110, 11042310)
TAG = re.compile(r"<[^>]+>")
EVOLVE = re.compile(r"<(ev|sev)>.*?</\1>", re.S)


def load(lang):
    out = {}
    for path in sorted(RAW.glob(f"**/set_*_{lang}.json")):
        data = json.loads(path.read_text(encoding="utf-8"))["data"]
        for detail in (data.get("card_details") or {}).values():
            c = detail["common"]
            out[c["card_id"]] = (c["name"], c.get("skill_text") or "")
    return out


def blocks(skill):
    """Ability blocks: lines and <hr> sections, evolve blocks kept as their own blocks."""
    out = []
    for m in EVOLVE.finditer(skill or ""):
        out += [TAG.sub("", s).strip() for s in re.split(r"\n|<hr>", m.group(0))]
    base = EVOLVE.sub("", skill or "")
    out = [TAG.sub("", s).strip() for s in re.split(r"\n|<hr>", base)] + out
    return [b for b in out if b]


def sentences(block, lang):
    if lang in ("ja", "chs", "cht"):
        parts = re.split(r"(?<=[。])", block)
    else:
        parts = re.split(r"(?<=[.!?])\s+", block)
    return [p.strip() for p in parts if p.strip()]


def main():
    langs = {l: load(l) for l in ("ja", "en", "chs", "cht", "ko")}
    langs = {l: v for l, v in langs.items() if v}
    print("languages present:", {l: len(v) for l, v in langs.items()})
    print("\n1. The two cards")
    for cid in TARGETS:
        for l, v in langs.items():
            if cid in v:
                name, skill = v[cid]
                print(f"  {cid} [{l}] {name}: " + " | ".join(blocks(skill)))
    ja, en = langs.get("ja", {}), langs.get("en", {})
    kinds = Counter()
    agree = defaultdict(Counter)
    examples = []
    for cid, (name, skill) in ja.items():
        jb = blocks(skill)
        for bi, b in enumerate(jb):
            ss = sentences(b, "ja")
            for si, s in enumerate(ss):
                if "なら、" not in s and "ならば、" not in s:
                    continue
                rest = s.split("なら、", 1)[-1] if "なら、" in s else s.split("ならば、", 1)[-1]
                if "、" in rest:
                    kinds["joined (two clauses after the if, one sentence)"] += 1
                if si + 1 < len(ss) and "なら" not in ss[si + 1]:
                    kinds["split"] += 1
                    for l in ("en", "chs", "cht", "ko"):
                        if l not in langs or cid not in langs[l]:
                            continue
                        ob = blocks(langs[l][cid][1])
                        if len(ob) != len(jb):
                            agree[l]["blocks differ"] += 1
                            continue
                        d = len(sentences(ob[bi], l)) - len(ss)
                        agree[l]["same count" if d == 0 else ("fewer" if d < 0 else "more")] += 1
                        if l == "en" and d < 0 and len(examples) < 40:
                            examples.append((cid, en.get(cid, ("?",))[0]))
                break
    print("\n2. JA blocks with a 「なら、」 sentence:", dict(kinds))
    print("\n3. For the JA 'split' blocks, the same block in other languages (sentence count vs JA):")
    for l, c in agree.items():
        print(f"  {l}: {dict(c)}")
    print("\n4. JA split but EN has fewer sentences (EN merged a sentence), first 40:")
    for cid, n in examples:
        print(f"  {cid} {n}")


if __name__ == "__main__":
    main()
