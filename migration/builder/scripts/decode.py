import json,sys,base64,collections,re
names={}
for lang in ['en','ja']:
    for sid in [10000,10001,10002,10003,10004,10005,10006,10007,10008,10009,90000]:
        f=f'set_{sid}.json' if lang=='en' else f'set_{sid}_{lang}.json'
        d=json.load(open(f))['data']
        for k,v in d['card_details'].items():
            c=v['common']
            names.setdefault(int(k),{})[lang]=c['name']
            names[int(k)]['cost']=c['cost']; names[int(k)]['set']=c['card_set_id']; names[int(k)]['rot']=c['is_include_rotation']; names[int(k)]['rar']=c['rarity']; names[int(k)]['cls']=c['class']; names[int(k)]['tok']=c['is_token']
def dec(code):
    b=base64.urlsafe_b64decode(code+'=='*0 if len(code)%4==0 else code+'='*(4-len(code)%4))
    return int.from_bytes(b,'big')
h=sys.argv[1]
parts=h.split('.')
print('header',parts[:2], 'n cards',len(parts)-2)
cnt=collections.Counter(parts[2:])
order=[]
for p in parts[2:]:
    if p not in order: order.append(p)
tot=0
for p in order:
    cid=dec(p)
    n=names.get(cid,{})
    tot+=cnt[p]
    print(f"{cnt[p]}x {cid} {n.get('cost')}pp {n.get('en')} / {n.get('ja')} set={n.get('set')} rot={n.get('rot')} R{n.get('rar')}")
print('total',tot)
