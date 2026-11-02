import json,sys,subprocess,collections,urllib.parse
h=sys.argv[1]; lang=sys.argv[2] if len(sys.argv)>2 else 'en'
out=subprocess.run(['curl','-sS','https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash='+urllib.parse.quote(h,safe='.-_'),'-H','Lang: '+lang,'-H','Accept: application/json'],capture_output=True,text=True).stdout
d=json.loads(out)['data']
print([k for k in d.keys()])
for k,v in d.items():
    if k not in ('cards','card_details','tribe_names','specific_effect_type_names','specific_effect_card_info'):
        print(k, json.dumps(v,ensure_ascii=False)[:600])
