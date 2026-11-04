import sys, json
sys.path.insert(0, "/home/user/test1")
from svsim.tools import records
from svsim.core.actions import from_dict
from svsim.core.engine import apply
from svsim.ui.text import card_name
rec = json.load(open("det_record.json"))
warm = len(sys.argv) > 1
st = records.start(rec)
for k, data in enumerate(rec["actions"][:7]):
    apply(st, from_dict(data))
card = st.in_hand(st.active, 32)
print("uid 32 =", card_name(card.defn), card.defn.card_id, "| 连击", st.players[st.active].combo)
if warm:
    from svsim.search.combo import profile
    for c in st.players[st.active].hand: profile(c.defn)
    print("（已先调用 profile 预热）")
before = [c.uid for c in st.players[st.active].hand]
apply(st, from_dict(rec["actions"][7]))
print("打出后手牌:", [(c.uid, card_name(c.defn)) for c in st.players[st.active].hand])
