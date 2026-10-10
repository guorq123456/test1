"""Every model's logit (repr) on the ENDED positions of the first N step-1 self-play games, for comparing two
versions of the code bit for bit: run it from each checkout and compare the files. Models: the installed Ramp
mirror turn-end model, cand-kc-ramp-ramp, cand-nl-ramp-ramp. Condition: the opponent's deck list is known (order and
hand not).
usage: logits_dump.py STEP1_DIR OUT.json [GAMES]"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main():
    d, out = sys.argv[1], sys.argv[2]
    games = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    sys.path.insert(0, f"{d}/ana")
    import student_data as SD
    from svsim.learn.model import LinearValue
    from svsim.learn.netdata import ENDED, rows
    P = ROOT / "svsim/learn/phased_models"
    files = {"installed": P / "ramp-ramp-ended.json", "cand-kc": P / "cand-kc-ramp-ramp/ramp-ramp-ended.json",
             "cand-nl": P / "cand-nl-ramp-ramp/ramp-ramp-ended.json"}
    recs = list(SD._lines(f"{d}/selfplay.jsonl"))[:games]
    ends = [(st, me) for rec in recs for ph, me, st, res in rows(rec) if ph == ENDED]
    res = {}
    for name, f in files.items():
        m = LinearValue.load(f)
        res[name] = [repr(m.logit(st, me)) for st, me in ends]
    Path(out).write_text(json.dumps(res))
    print(len(ends), "turn ends")


if __name__ == "__main__":
    main()
