"""Where each player finished in each event (data/placements.csv), for the site's tooltips.

* Challonge brackets carry final_rank for every participant (all completed brackets).
* Elimination stages elsewhere (start.gg / Battlefy top cuts, the World Championship grand finals
  entered from official news) are ranked from the bracket itself: a player's place depends on the
  round they were knocked out in, ties share a range ("第 5–8 名").
* Otherwise the label is the stage and the player's record in it ("瑞士轮 4-2").
An event's label uses the deepest stage the player reached.
"""
import csv
import glob
import json
import os
import re
from collections import defaultdict

from normalize import DEPTH, MAIN, PLACEHOLDER, TAG, challonge_event, norm_name, stage_name  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def account_map():
    out = {}
    for p in csv.DictReader(open(os.path.join(DATA, "players.csv"))):
        for a in p["accounts"].split():
            out[a] = p["player_id"]
    return out


def challonge_ranks(accounts):
    """{(event, stage label): {pid: (rank, field size)}} from Challonge final_rank."""
    out = defaultdict(dict)
    for f in sorted(glob.glob(os.path.join(DATA, "raw", "challonge", "*.json"))):
        t = json.load(open(f))["tournament"]
        event, stage = challonge_event(t["name"], t.get("started_at") or t.get("start_at") or t.get("created_at"))
        label = stage_name(event, stage, t.get("tournament_type"))
        parts = [x["participant"] for x in t.get("participants", [])]
        ranked = [p for p in parts if p.get("final_rank")]
        for p in ranked:
            display = TAG.sub("", p.get("display_name") or p.get("name") or "").strip()
            if PLACEHOLDER.match(display):
                continue
            node = "ch:" + (p.get("challonge_username") or norm_name(display) or str(p["id"]))
            pid = accounts.get(node)
            if pid:
                out[(event, label)][pid] = (p["final_rank"], len(ranked))
    return out


def elimination_ranks(rows):
    """Rank players of single/double elimination stages (non-Challonge) by the round they went out in."""
    out = {}
    stages = defaultdict(list)
    for r in rows:
        if r["source"] == "challonge" or not r["winner"] or r["winner"] == "0":
            continue
        lab = stage_name(r["event"], r["stage"], r["stage_type"])
        if lab in ("总决赛", "8 强", "16 强", "32 强", "淘汰赛"):
            stages[(r["event"], lab)].append(r)
    for key, ms in stages.items():
        double = any("double" in (m["stage_type"] or "") for m in ms)
        ms.sort(key=lambda m: m["time"])
        losses, out_at, players = defaultdict(int), {}, set()
        third = [m for m in ms if re.search(r"3rd", str(m["round"]), re.I)]
        for i, m in enumerate(ms):
            w, l = (m["p1"], m["p2"]) if m["winner"] == "1" else (m["p2"], m["p1"])
            players |= {w, l}
            if m in third:
                continue
            losses[l] += 1
            if losses[l] == (2 if double else 1):
                out_at[l] = i
        # later knock-outs rank higher; single elimination players out in the same round share a range
        rank = {}
        champs = [p for p in players if p not in out_at]
        for p in champs:
            rank[p] = (1, 1)
        order = sorted(out_at, key=lambda p: -out_at[p])
        pos = len(champs) + 1
        groups = []
        for p in order:
            rnd = None if double else ms[out_at[p]]["round"]  # the round they were knocked out in
            if groups and not double and groups[-1][0] == rnd:
                groups[-1][1].append(p)
            else:
                groups.append((rnd, [p]))
        for _, ps in groups:
            for p in ps:
                rank[p] = (pos, pos + len(ps) - 1)
            pos += len(ps)
        for m in third:  # a 3rd-place match splits the shared 3-4 range
            w, l = (m["p1"], m["p2"]) if m["winner"] == "1" else (m["p2"], m["p1"])
            rank[w], rank[l] = (3, 3), (4, 4)
        out[key] = rank
    return out


def main():
    rows = list(csv.DictReader(open(os.path.join(DATA, "matches.csv"))))
    rec = defaultdict(lambda: [0, 0])
    reached = defaultdict(dict)  # (event, pid) -> {stage label: True}
    for r in rows:
        if r["valid"] != "1":
            continue
        lab = stage_name(r["event"], r["stage"], r["stage_type"])
        w, l = (r["p1"], r["p2"]) if r["winner"] == "1" else (r["p2"], r["p1"])
        rec[(r["event"], lab, w)][0] += 1
        rec[(r["event"], lab, l)][1] += 1
        reached[(r["event"], w)][lab] = True
        reached[(r["event"], l)][lab] = True
    ch = challonge_ranks(account_map())
    el = elimination_ranks(rows)

    out = []
    for (event, pid), labs in reached.items():
        deepest = max(labs, key=lambda x: DEPTH.get(x, 0))
        place = None
        if (event, deepest) in el and pid in el[(event, deepest)]:
            a, b = el[(event, deepest)][pid]
            place = f"第 {a} 名" if a == b else f"第 {a}–{b} 名"
        elif (event, deepest) in ch and pid in ch[(event, deepest)] and deepest not in ("瑞士轮", "小组赛"):
            place = f"第 {ch[(event, deepest)][pid][0]} 名"
        w, l = rec[(event, deepest, pid)]
        if place:
            label = f"{deepest} · {place}"
        else:
            label = f"{deepest} {w}-{l}"
        if place:
            label += f"（{w}-{l}）"
        out.append({"event": event, "player_id": pid, "label": label})
    with open(os.path.join(DATA, "placements.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["event", "player_id", "label"])
        wr.writeheader()
        wr.writerows(sorted(out, key=lambda r: (r["event"], r["label"])))
    print(f"data/placements.csv: {len(out)} rows")


if __name__ == "__main__":
    main()
