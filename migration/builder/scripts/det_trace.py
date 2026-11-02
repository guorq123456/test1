import sys, json
sys.path.insert(0, "/home/user/test1")
from svsim.tools import records
from svsim.ui.text import describe
rec = json.load(open("det_record.json"))
out = []
for i, (st, a) in enumerate(records.steps(rec)):
    fp = (st.rng.getstate()[1][:3], [[c.uid for c in p.deck][-5:] for p in st.players],
          [[c.uid for c in p.hand] for p in st.players], [[(c.uid, c.atk, c.life) for c in p.field] for p in st.players],
          [p.leader_hp for p in st.players])
    out.append((i, str(a), json.dumps(fp)))
json.dump(out, open(sys.argv[1], "w"))
