"""R1 relabel (registered in the README before any relabelled data): the move prior's training decisions searched
again by A's scorer without a prior (UCB1, N 200: D10's A-UCB), the new root visits written where the old ones were.
Condition: the opponent's deck list is known (order and hand not).

    cd <checkout of fbb3c21> && PYTHONPATH=. python3 relabel.py OUT_DIR REC.jsonl.gz [REC ...] --workers 3

Population: learn.setpolicy.decisions (searched main-phase decisions with two distinct moves or more). A decision
(record seed s, game g, step i) is kept when crc32("r1-ramp-keep/s/g/i") is even (about half); its search seed is
crc32("r1-ramp-seed/s/g/i"). Each kept decision gets a fresh agent (no state carried between decisions or games).
Output: the same record with "search"[i] = {"visits": per legal move (a key's count repeated for each of its moves,
0 for a key the root never opened), "visits0": the recorded visits} at a kept decision whose root was searched, and
None everywhere else (a kept decision the agent played without searching is dropped and counted). A shard is
written to a temporary file and renamed when complete; an existing output is skipped.
"""
import argparse, gzip, json, os, sys, zlib
from multiprocessing import Pool

P = "plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M = "analysis/scaling/models"
SPEC = f"mcts:200+{P}+setnet={M}/net-mid-ramp-t.npz+netmid"


def keep(s, g, i):
    return zlib.crc32(f"r1-ramp-keep/{s}/{g}/{i}".encode()) % 2 == 0


def seed_of(s, g, i):
    return zlib.crc32(f"r1-ramp-seed/{s}/{g}/{i}".encode())


def _game(line):
    from svsim.core.engine import legal_actions
    from svsim.learn.netdata import _search
    from svsim.learn.setpolicy import decisions, distinct
    from svsim.search.mcts import _locator, action_key
    from svsim.tools.arena import make_agent
    rec = json.loads(line)
    s, g = rec["seed"], rec["g"]
    old = rec.get("search") or []
    new = [None] * len(old)
    st = {"decisions": 0, "kept": 0, "searched": 0, "outer": 0, "unmatched": 0}
    for i, state, legal, reps, group, pi, start in decisions(rec):
        st["decisions"] += 1
        if not keep(s, g, i):
            continue
        st["kept"] += 1
        agent = make_agent(SPEC, seed_of(s, g, i))
        search = _search(agent)
        search.last_root = None
        x = state.clone()
        agent.act(x, legal_actions(x))
        root = search.last_root
        if root is None or not root.children:
            st["outer"] += 1
            continue
        where = _locator(state, state.active)
        pos = {action_key(state, a, where): n for n, a in enumerate(reps)}
        kv = [0] * len(reps)
        for k, child in root.children.items():
            if k in pos:
                kv[pos[k]] = child.visits
            else:
                st["unmatched"] += 1
        new[i] = {"visits": [kv[group[j]] for j in range(len(legal))], "visits0": old[i]["visits"]}
        st["searched"] += 1
    rec["search"] = new
    rec["relabel"] = {"spec": SPEC, "code": "fbb3c21", "registered": "README R1"}
    return json.dumps(rec, separators=(",", ":")), st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("records", nargs="+")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--max-games", type=int, default=0, help="smoke tests only")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for path in args.records:
        dst = os.path.join(args.out, os.path.basename(path))
        if os.path.exists(dst):
            print("skip", dst, flush=True)
            continue
        lines = [x for x in gzip.open(path, "rt") if x.strip()]
        if args.max_games:
            lines = lines[:args.max_games]
        tot = {}
        tmp = dst + ".part"
        with Pool(args.workers) as pool, gzip.open(tmp, "wt") as fh:
            for out, st in pool.imap(_game, lines, chunksize=2):
                fh.write(out + "\n")
                for k, v in st.items():
                    tot[k] = tot.get(k, 0) + v
        os.replace(tmp, dst)
        json.dump(tot, open(dst.replace(".jsonl.gz", ".stats.json"), "w"))
        print(os.path.basename(path), json.dumps(tot), flush=True)


if __name__ == "__main__":
    main()
