# Generate rule files rule_fine.py and rule_coarse.py with embedded lookup tables (from build_tables.py output).
import json
fine=json.load(open('table_fine.json')); coarse=json.load(open('table_coarse.json'))
def tup(s): return tuple(int(x) for x in s.split(',')) if s else ()
F={}
for k,v in fine.items():
    r,S,Rb=k.split('|'); F[(int(r),tup(S),tup(Rb))]=tuple(v)
C={}
for k,v in coarse.items():
    r,R=k.split('|'); C[(int(r),tup(R))]=tuple(v)
common='''
def _parts(r,a):
    a2=sorted(x for x in a if x>1)              # [1]_q = 1 is a trivial factor
    has0=any(x%r==0 for x in a2)
    F=sum(x//r for x in a2)
    S=tuple(x for x in a2 if x<r)               # small factors 1<a_i<r
    Rb=tuple(sorted(x%r for x in a2 if x>r))    # residues of big factors a_i>r (r|a_i excluded via has0)
    R=tuple(sorted(x%r for x in a2))            # residues of all nontrivial factors
    return a2,has0,F,S,Rb,R
def domain(r,a):
    return 2<=r<=6 and sum(1 for x in a if x>1)<=8
'''
with open('rule_fine.py','w') as f:
    f.write('# Rule A (fine lookup, fitted on the full fit box r<=6, k<=8, a_i<=12, b<=60; 0 fit errors).\n')
    f.write('# P unimodal iff (some r|a_i) or d<=0 or d in E[(r,S,Rb)], where d=b-1-F.\n')
    f.write(common)
    f.write('E='+repr(F)+'\n')
    f.write('''
def predict(r,a,b):
    a2,has0,F,S,Rb,R=_parts(r,a)
    if has0: return True
    d=b-1-F
    if d<=0: return True
    return d in E.get((r,S,Rb),())
''')
with open('rule_coarse.py','w') as f:
    f.write('# Rule B (coarse lookup on residue multiset only, fitted on the full fit box; 24 fit errors, all r=6, R=(2,2,3,4,4,4,4,4)).\n')
    f.write('# P unimodal iff (some r|a_i) or d<=0 or d in E[(r,R)], where d=b-1-F, R = residues of a_i>1.\n')
    f.write(common)
    f.write('E='+repr(C)+'\n')
    f.write('''
def predict(r,a,b):
    a2,has0,F,S,Rb,R=_parts(r,a)
    if has0: return True
    d=b-1-F
    if d<=0: return True
    return d in E.get((r,R),())
''')
print('fine entries',len(F),'coarse entries',len(C))
