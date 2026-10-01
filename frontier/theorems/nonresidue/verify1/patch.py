s=open('wheel.c').read()
s=s.replace("if(!ok){ // fallback direct Jacobi on all k<=s",
 "if(!ok && s*s==m){ ok=1; sq++; } // perfect square r^2: J(lpf(r),m)=0 with lpf(r)<=r=s, so f(m)<=s\n      if(!ok){ fb++; // fallback direct Jacobi on all k<=s")
s=s.replace("u64 found=0, cand=0;","u64 found=0, cand=0, sq=0, fb=0;")
s=s.replace("reduction(+:found,cand)","reduction(+:found,cand,sq,fb)")
s=s.replace('printf("X=%llu candidates','printf("squares=%llu fallbacks=%llu ",(unsigned long long)sq,(unsigned long long)fb); printf("X=%llu candidates')
open('wheel2.c','w').write(s)
