import random
N=200000
def draw_hand(deck,keep):
    random.shuffle(deck)
    hand=deck[:4]; rest=deck[4:]
    kept=[c for c in hand if keep(c)]; tossed=[c for c in hand if not keep(c)]
    hand=kept+rest[:len(tossed)]; rest=rest[len(tossed):]+tossed
    random.shuffle(rest)
    return hand,rest
def ramp(first, flex_keep_zooey=None):
    deck=['sign']*3+['lum']*3+['zoo']*3+['bur']*3+['x']*28
    keepz = first if flex_keep_zooey is None else flex_keep_zooey
    res={'j1_by3':0,'j2_by4':0,'bur_by7':0,'both':0}
    for _ in range(N):
        hand,rest=draw_hand(deck[:], lambda c: c in('sign','lum') or (c=='zoo' and keepz))
        maxpp=0; jumps=0; extra=0 if first else 1; j1=False; j2=False
        for t in range(1,8):
            hand.append(rest.pop(0))
            maxpp=min(10,maxpp+1); pp=maxpp
            if not first and extra and t>=2 and t<=5:
                # use extra pp if it enables a jump this turn
                if (pp+1>=3 and any(c in('sign','lum') for c in hand) and pp<3) or (pp+1>=5 and 'zoo' in hand and pp<5):
                    pp+=1; extra=0
            while True:
                if 'zoo' in hand and pp>=5 and t<=6: hand.remove('zoo'); pp-=5; maxpp+=1; jumps+=1; continue
                c=next((c for c in hand if c in('sign','lum')),None)
                if c and pp>=3 and t<=6: hand.remove(c); pp-=3; maxpp+=1; jumps+=1; continue
                break
            if (t==3 if first else t==2) and jumps>=1: j1=True
            if (t==4 if first else t==3) and jumps>=2: j2=True
        b='bur' in hand
        res['j1_by3']+=j1; res['j2_by4']+=j2; res['bur_by7']+=b; res['both']+=(j2 and b)
    return {k:round(v/N,3) for k,v in res.items()}
def elf(first):
    deck=['thes']*3+['wog']*3+['x']*34
    tgt=5 if first else 4; hit=0
    for _ in range(N):
        hand,rest=draw_hand(deck[:], lambda c:c in('thes','wog'))
        hand+=rest[:tgt]
        hit+='thes' in hand
    return round(hit/N,3)
print('ramp first',ramp(True)); print('ramp second',ramp(False))
print('elf thestae by evolve turn first',elf(True),'second',elf(False))
