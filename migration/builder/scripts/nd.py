import json,sys,re,html,subprocess
id=sys.argv[1]; lang=sys.argv[2] if len(sys.argv)>2 else 'en'
out=subprocess.run(['curl','-sS',f'https://shadowverse-wb.com/web/Information/detail?id={id}','-H',f'Lang: {lang}'],capture_output=True).stdout
d=json.loads(out)['data']
def walk(o,depth=0):
    if isinstance(o,dict):
        for k,v in o.items():
            if isinstance(v,str) and ('<' in v or len(v)>200):
                t=re.sub(r'<br\s*/?>','\n',v); t=re.sub(r'</(p|li|h\d|tr|div)>','\n',t); t=re.sub(r'<[^>]+>','',t); t=html.unescape(t)
                print(re.sub(r'\n\s*\n+','\n',t))
            elif isinstance(v,(dict,list)): walk(v,depth+1)
            else:
                if k in ('title','display_start_time'): print(k,':',v)
    elif isinstance(o,list):
        for x in o: walk(x,depth+1)
walk(d)
