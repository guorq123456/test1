# Check every "Empirical" formula (closed form, recurrence, g.f.) in A253152, A253428-A253441
# against the theorem's values for the first 400 terms.
import re, subprocess, sympy as sp
exec(open('/tmp/claude-0/deep/hardin-table/compare_all.py').read().split("vals={}")[0])  # import T()
x=sp.symbols('x')
seqs={'A253152':('col',1),'A253429':('col',2),'A253430':('col',3),'A253431':('col',4),'A253432':('col',5),'A253433':('col',6),
      'A253434':('col',7),'A253436':('row',2),'A253437':('row',3),'A253438':('row',4),'A253439':('row',5),'A253440':('row',6),
      'A253441':('row',7),'A253428':('diag',0)}
N=400
for a,(typ,c) in seqs.items():
    txt=subprocess.run(['git','-C','/tmp/claude-0/oeis/oeisdata','show',f'HEAD:seq/A253/{a}.seq'],capture_output=True,text=True).stdout
    seq=[T(i,c) if typ=='col' else (T(c,i) if typ=='row' else T(i,i)) for i in range(1,N+1)]
    data=[int(t) for l in txt.splitlines() if l[:2] in ('%S','%T','%U') for t in l.split(None,2)[2].strip().strip(',').split(',')]
    assert data==seq[:len(data)], a
    msgs=[]
    for l in txt.splitlines():
        if not l.startswith('%F'): continue
        m=re.search(r'a\(n\) = 9\*2\^(n|\(n-1\)) \+ (\d+) for n\s*>\s*(\d+)',l)
        if m:
            e,cst,n0=m.group(1),int(m.group(2)),int(m.group(3))
            ok=all(seq[n-1]==9*(2**n if e=='n' else 2**(n-1))+cst for n in range(n0+1,N+1))
            sharp = not (seq[n0-1]==9*(2**n0 if e=='n' else 2**(n0-1))+cst)
            msgs.append(f"closed form n>{n0}: {ok} (fails at n={n0}: {sharp})")
        m=re.search(r'a\(n\) = 3\*a\(n-1\) ?-2\*a\(n-2\) for n\s*>\s*(\d+)',l.replace(' - ',' -'))
        if m:
            n0=int(m.group(1)); ok=all(seq[n-1]==3*seq[n-2]-2*seq[n-3] for n in range(n0+1,N+1))
            sharp = not (seq[n0-1]==3*seq[n0-2]-2*seq[n0-3]) if n0>=3 else None
            msgs.append(f"recurrence n>{n0}: {ok} (fails at n={n0}: {sharp})")
        m=re.search(r'g\.f\.: (.*?)\. -',l)
        if m:
            g=sp.sympify(m.group(1).replace('^','**'))
            ser=sp.Poly(sp.series(g,x,0,61).removeO(),x).all_coeffs()[::-1]
            ok=[int(t) for t in ser[1:61]]==seq[:60]
            msgs.append(f"g.f. (first 60 coeffs; rational with denominator (1-x)(1-2x), so identical forever once recurrence region reached): {ok}")
    print(a,typ,c,"data ok;",'; '.join(msgs))
