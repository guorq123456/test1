import json,sys,subprocess,urllib.parse,collections,itertools
hs={'pirate':"1.2.cEZs.cEZs.cEZs.dmj6.dmj6.dmj6.dmyk.dmyk.dmyk.e9Ak.e9Ak.e9Ak.e9NO.e9NO.e9NO.eXnu.eXnu.eXnu.evm6.evm6.evm6.fgIM.fgIM.fgIM.fgX-.fgX-.fgX-.fgb6.fgb6.fgb6.fgnc.fgnc.fgnc.fgqk.fgqk.fgqk.fh1E.fh1E.fh1E.fh1O",
'lw':"1.5.cM8E.dtoY.dtoY.dtoY.eGCk.eGCk.eGCk.eegM.ef6e.ef6e.f0oG.f0oG.f0oG.f11k.f11k.f11k.f1KU.f1KU.f1KU.f1W-.f1W-.f1W-.f1X8.f1X8.f1X8.fPCm.fPCm.fPCm.fPxU.fndG.fndG.fndG.fnsk.fnsk.foL-.foL-.foL-.foM8.foM8.foM8",
'ramp':"1.4.cJl6.cJl6.cJl6.dhqm.dhqm.dhqm.drrO.drrO.drrO.e4IE.e4IE.eDpc.eDpc.eE3E.eE3E.eE3E.eEFk.eEFk.eEFk.ecgE.ecgE.ecgE.ecgO.ecgO.ecgO.e-Ls.e-Ls.e-Ls.e-ec.e_4k.e_4k.e_4k.fN08.fN08.fNVO.fNVO.fNVO.flvu.flvu.flvu",
'combo':"1.1.dhqc.e4Gg.e4Gg.e4Gg.e6FE.e6kU.e6x8.e6x8.e6x8.eVLe.eVLe.et1G.et4E.etl-.etl-.etl-.etm8.etm8.etm8.fGAU.fGAU.fGAU.fds6.fds6.fds6.fe5k.fe5k.fe5k.fe8s.fe8s.fe8s.feLM.feLM.feLM.fea-.fea-.fea-.feb8.feb8.feb8"}
rows=[]
for k,h in hs.items():
    out=subprocess.run(['curl','-sS','https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash='+urllib.parse.quote(h,safe='.-_'),'-H','Lang: en'],capture_output=True,text=True).stdout
    d=json.loads(out)['data']
    c=collections.Counter()
    for cid,n in d['deck_card_num'].items():
        c[d['card_details'][cid]['common']['rarity']]+=n
    rows.append((k,dict(c),d['total_red_ether']))
    print(k,dict(c),d['total_red_ether'])
for b,s,g,l in [(50,200,800,3500),(50,90,750,3500),(50,200,750,3500)]:
    print((b,s,g,l),[ r[1].get(1,0)*b+r[1].get(2,0)*s+r[1].get(3,0)*g+r[1].get(4,0)*l for r in rows])
