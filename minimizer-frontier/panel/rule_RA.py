"""Best rule found under the run-length lens (NOT exact for nu>=11).
Rule R_A on a nu-bit window W (nu odd):
  * rising edges = positions i with W[i]=0, W[i+1]=1.
  * no rising edge (W = 1^a 0^b): h = a mod 2.
  * otherwise h = parity of the index of a selected rising edge:
      stage 1: keep edges with max valley persistence pers = min(L,R) of the +-1 walk
               (L/R = rise before the walk goes strictly below the valley level, truncated at window ends);
               if the kept edges' parities have a strict majority -> that parity.
      stage 2: among them keep max max(a,b) (a = visible 0-run before edge, b = visible 1-run after); majority.
      stage 3: keep max persL = L+R; majority.   stage 4: keep edges nearest the window centre.
      otherwise rc-symmetrised fallback: h(W)=0 for the first-encountered member of the rc pair, h(rc W)=1.
Prints P(nu) excess (pnu.excess) and the odd-k charged-count excess (two embeddings)."""
import sys; sys.path.insert(0,'/home/user/test1/minimizer-frontier'); sys.path.insert(0, __import__('os').path.dirname(__file__))
import numpy as np
from pnu import excess
from w2 import charged_count, bound_charged
from stagesearch2 import build_h
ST=[('pers',1),'maj',('max',1),'maj',('persL',1),'maj',('centre',1)]
for nu in (3,5,7,9,11,13):
    h=build_h(nu,ST); n=nu+1; U=np.arange(1<<n); B=bound_charged(n)
    print('nu=%2d  P-excess=%3d   charged-excess(ignore last bit)=%3d  charged-excess(f=h(Delta S))=%3d'%(
        nu, excess(h,nu), charged_count(h[U>>1],n)-B, charged_count(h[(U^(U>>1))&((1<<nu)-1)],n)-B), flush=True)
