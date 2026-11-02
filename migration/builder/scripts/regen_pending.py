"""Rewrite svsim/cards/pending.py's PENDING from HEAD's, minus the ids given (8 per line)."""
import re, subprocess, sys
remove = {int(x) for x in sys.argv[1:]}
src = subprocess.run(["git", "show", "HEAD:svsim/cards/pending.py"], capture_output=True, text=True, check=True).stdout
m = re.search(r"PENDING = frozenset\(\{(.*?)\}\)", src, re.S)
ids = sorted({int(x) for x in re.findall(r"\d+", m.group(1))} - remove)
lines = [", ".join(map(str, ids[i:i + 8])) + "," for i in range(0, len(ids), 8)]
body = "PENDING = frozenset({\n" + "".join(f"    {l}\n" for l in lines) + "})"
open("svsim/cards/pending.py", "w").write(src[:m.start()] + body + src[m.end():])
print(len(ids), "pending")
