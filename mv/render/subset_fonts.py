import json, re, glob, os, subprocess, sys
MV='/home/user/test1/mv'; OUT=sys.argv[1] if len(sys.argv)>1 else 'dist_fonts'
os.makedirs(OUT, exist_ok=True)
chars=set(chr(c) for c in range(0x20,0x7F))
tl=json.load(open(f'{MV}/data/timeline.json',encoding='utf-8'))
def walk(o):
    if isinstance(o,str): chars.update(o)
    elif isinstance(o,dict): [walk(v) for v in o.values()]
    elif isinstance(o,list): [walk(v) for v in o]
walk(tl)
for f in glob.glob(f'{MV}/js/*.js')+[f'{MV}/index.html', f'{MV}/css/style.css']:
    chars.update(open(f,encoding='utf-8').read())
chars.update('「」『』（）【】…―—–・、。！？：；，．％＋－×÷＝〜～ー々〆〇０１２３４５６７８９ＡＢＣＤＥＦ　')
chars.update('机械的声音克你我他她它们这那是不了在有和就都而及与着或一个之为以于上下中')
chars={c for c in chars if ord(c)>=0x20 and c not in '  '}
txt=''.join(sorted(chars)); open(f'{OUT}/chars.txt','w',encoding='utf-8').write(txt)
print('glyph set:', len(chars), 'chars')
total_in=total_out=0
for src in sorted(glob.glob(f'{MV}/fonts/*.ttf')):
    name=os.path.basename(src); dst=f'{OUT}/{name}'
    r=subprocess.run(['pyftsubset',src,f'--text-file={OUT}/chars.txt','--layout-features=*','--glyph-names','--notdef-outline','--recalc-bounds','--recalc-average-width','--name-IDs=*','--retain-gids' if False else '--no-hinting',f'--output-file={dst}'],capture_output=True,text=True)
    if r.returncode: print('ERR',name,r.stderr[-300:]); continue
    i,o=os.path.getsize(src),os.path.getsize(dst); total_in+=i; total_out+=o
    print(f'{name:40s} {i/1e6:6.2f} MB -> {o/1e6:5.2f} MB')
print(f'TOTAL {total_in/1e6:.1f} MB -> {total_out/1e6:.2f} MB')
