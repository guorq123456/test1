import subprocess, math, numpy as np, os, sys
from box import in_box
from win import Inst
HERE=os.path.dirname(os.path.abspath(__file__))
def get_inst(r,a):
    assert in_box(r,a), "outside fit box"
    bits=sum(math.log2(x) for x in a)+8; W=int(bits//64)+2
    out=subprocess.run([HERE+"/dumpdelta",str(W),str(r)]+[str(x) for x in a],capture_output=True,text=True).stdout.split("\n")
    r_,k,D,F,E=map(int,out[0].split())
    d=np.array([float(l) for l in out[1:] if l.strip()])
    return Inst(r,D,F,d)
