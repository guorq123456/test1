import json,sys,subprocess,urllib.parse
h=sys.argv[1]
def get(lang):
    out=subprocess.run(['curl','-sS','https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash='+urllib.parse.quote(h,safe='.-_'),'-H','Lang: '+lang,'-H','Accept: application/json'],capture_output=True,text=True).stdout
    return json.loads(out)['data']
en=get('en'); ja=get('ja')
cls={0:'Neutral',1:'Forest',2:'Sword',3:'Rune',4:'Dragon',5:'Abyss',6:'Haven',7:'Portal'}
rar={1:'Bronze',2:'Silver',3:'Gold',4:'Legendary'}
print('class',cls[en['class_id']],'format',en['battle_format'],'red ether',en['total_red_ether'],'F/S/A',en['num_follower'],en['num_spell'],en['num_amulet'])
tot=0
for cid in en['sort_card_id_list']:
    n=en['deck_card_num'][str(cid)]; tot+=n
    c=en['card_details'][str(cid)]['common']; cj=ja['card_details'][str(cid)]['common']
    print(f"{n}x | {c['cost']} | {c['name']} | {cj['name']} | {cls[c['class']]} | {rar[c['rarity']]} | set {c['card_set_id']} | rot={c['is_include_rotation']}")
print('total',tot)
