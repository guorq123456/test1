import re

p = 'svsim/cards/sword.py'
s = open(p).read()
s = s.replace("""from svsim.cards import common
from svsim.cards.pool import card
""", """from svsim.cards import common
from svsim.cards.neutral import DIVINE_EVIDENCE
from svsim.cards.pool import card
""", 1)
consts = '''# --- set 10010 ---
GUILELESS_NEWSIE = card(11021110)  # 纯真卖报人
BEJEWELED_LADY = card(11021120)  # 宝石淑女
ONWARD_CHARGE = card(11021310)  # 突击号令
CHEEKY_ARCHITECT = card(11022110)  # 俏皮设计师
ERRANT_KNIGHT = card(11022120)  # 变心卫士
DICHOTOMOUS_FORENSICS = card(11022310)  # 表里的现场验证
PLACID_DILETTANTE = card(11023110)  # 安逸爱好家
NO_LIFES_CROSS_EXAMINATION = card(11023310)  # 诺·莱芙的问答
NO_LIFE = card(11024110)  # 表里侦探·诺·莱芙
ALMAELYS = card(11024120)  # 千金大参谋·阿尔梅莉洁
ALMAELYS_CREST = card(11024122)  # 纹章：千金大参谋·阿尔梅莉洁

'''
i = s.index("# --- set 10009 ---\n")
s = s[:i] + consts + s[i:]
scripts = open('/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/sword_scripts.txt').read()
i = s.index("# --- set 10009 -----------")
s = s[:i] + scripts + s[i:]
s = s.replace("""ALL_CARDS = CARDS + [
""", """ALL_CARDS = CARDS + [
    GUILELESS_NEWSIE, BEJEWELED_LADY, ONWARD_CHARGE, CHEEKY_ARCHITECT, ERRANT_KNIGHT,
    DICHOTOMOUS_FORENSICS, PLACID_DILETTANTE, NO_LIFES_CROSS_EXAMINATION, NO_LIFE, ALMAELYS,
""", 1)
old = "ALL_LEADER_AREA = LEADER_AREA + [GILDARIA_CREST, MAJESTIC_CONQUEST_CREST]"
assert old in s
s = s.replace(old, "ALL_LEADER_AREA = LEADER_AREA + [GILDARIA_CREST, MAJESTIC_CONQUEST_CREST, ALMAELYS_CREST]")
open(p, 'w').write(s)

p = 'svsim/cards/pending.py'
s = open(p).read()
ids = {11021110, 11021120, 11021310, 11022110, 11022120, 11022310, 11023110, 11023310, 11024110,
       11024120, 11024122}
head, rest = s.split("PENDING = frozenset({", 1)
body, tail = rest.split("})", 1)
nums = [int(x) for x in re.findall(r"\d+", body)]
left = [n for n in nums if n not in ids]
print(len(nums), len(left))
lines = ["    " + ", ".join(map(str, left[k:k + 8])) + "," for k in range(0, len(left), 8)]
s = head + "PENDING = frozenset({\n" + "\n".join(lines) + "\n})" + tail
open(p, 'w').write(s)
