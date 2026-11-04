"""Merge the ramp-t mirror's G_end pieces into one gend.jsonl / gend_ends.jsonl.gz (the architecture thread 2026-10-13
23:58Z; split by start between this machine and the analysis line, and resumed after interruptions).
Checks: every start of starts.jsonl appears exactly once; each start's turn-end rows number K x its plans (only
complete starts are kept from each piece, and a start found complete in two pieces must have identical result rows
apart from the cpu time: the determinism check). Condition: the opponent's deck list is known (order and hand not).
usage: krt_merge.py DATA_DIR OUT_DIR PIECE_ROWS:PIECE_ENDS [...]"""
import gzip, json, sys, zlib
from collections import Counter, defaultdict


def read_ends(path):
    raw = open(path, "rb").read()
    txt = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(raw).decode("utf-8", "ignore") if raw else ""
    out = defaultdict(list)
    for line in txt.split("\n"):
        try:
            r = json.loads(line)
        except Exception:                          # noqa: BLE001 (a cut-off last line)
            continue
        out[r["n"]].append(line)
    return out


def main():
    data, out_dir, pieces = sys.argv[1], sys.argv[2], sys.argv[3:]
    starts = {json.loads(l)["k"]: json.loads(l) for l in open(f"{data}/starts.jsonl") if l.strip()}
    plans = {json.loads(l)["k"]: len(json.loads(l)["plans"]) for l in open(f"{data}/plans.jsonl") if l.strip()}
    rows, ends, same, differ = {}, {}, 0, 0
    for piece in pieces:
        rp, ep = piece.split(":")
        pe = read_ends(ep)
        for line in open(rp):
            try:
                r = json.loads(line)
            except Exception:                      # noqa: BLE001
                continue
            k = r["k"]
            if len(pe.get(k, ())) != r["K"] * plans[k]:
                continue
            strip = {a: b for a, b in r.items() if a != "cpu"}
            if k in rows:
                if {a: b for a, b in rows[k].items() if a != "cpu"} == strip:
                    same += 1
                else:
                    differ += 1
                continue
            rows[k], ends[k] = r, pe[k]
    missing = sorted(set(starts) - set(rows))
    extra = sorted(set(rows) - set(starts))
    split = Counter(starts[k]["split"] for k in rows)
    with open(f"{out_dir}/gend.jsonl", "w") as fh:
        for k in sorted(rows):
            fh.write(json.dumps(rows[k]) + "\n")
    with gzip.open(f"{out_dir}/gend_ends.jsonl.gz", "wt") as fe:
        for k in sorted(ends):
            for line in ends[k]:
                fe.write(line + "\n")
    print(json.dumps({"starts": len(rows), "missing": missing[:20], "n_missing": len(missing), "extra": extra,
                      "split": dict(split), "ends": sum(len(v) for v in ends.values()),
                      "duplicates_identical": same, "duplicates_different": differ}))
    if missing or extra or differ:
        sys.exit(1)


if __name__ == "__main__":
    main()
