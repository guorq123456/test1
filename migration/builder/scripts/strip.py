import re,html,sys
s=open(sys.argv[1],encoding='utf-8').read()
s=re.sub(r'<script.*?</script>','',s,flags=re.S)
s=re.sub(r'<style.*?</style>','',s,flags=re.S)
t=re.sub(r'<[^>]+>','\n',s)
t=html.unescape(t)
lines=[l.strip() for l in t.split('\n') if l.strip()]
print('\n'.join(lines))
