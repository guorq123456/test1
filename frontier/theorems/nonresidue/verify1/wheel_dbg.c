// Check: for odd m in (529, X], f(m)^2 <= m, i.e. some k <= sqrt(m) has J(k,m) != 1.
// Wheel over primes 2..23 (period L = 8*3*5*...*23) keeps only m with J(p,m)=1 for p<=23,
// then tests further primes p (29..) with J(p,m) via table lookup mod 4p, then Jacobi fallback.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <omp.h>
typedef uint64_t u64; typedef __uint128_t u128;
static int jacobi(u64 a, u64 n){ int r=1; a%=n;
  while(a){ int tz=__builtin_ctzll(a); a>>=tz;
    if((tz&1)&&((n&7)==3||(n&7)==5)) r=-r;
    if((a&3)==3&&(n&3)==3) r=-r;
    u64 t=a; a=n%t; n=t; }
  return n==1?r:0; }
static u64 isqrt(u64 x){ u64 r=(u64)sqrtl((long double)x); while(r*r>x) r--; while((r+1)*(r+1)<=x) r++; return r; }
int main(int argc,char**argv){
  u64 X=strtoull(argv[1],0,10);
  int wp[]={3,5,7,11,13,17,19,23}; int nw=8;
  // build residues mod L
  u64 L=8; u64 *res=malloc(sizeof(u64)*2); int nr=0; res[nr++]=1; res[nr++]=7; // J(2,m)=1 iff m=+-1 mod 8
  for(int w=0;w<nw;w++){ u64 p=wp[w]; u64 *nres=malloc(sizeof(u64)*nr*p); int nn=0;
    for(int i=0;i<nr;i++) for(u64 j=0;j<p;j++){ u64 r=res[i]+j*L; if(jacobi(p,r)==1) nres[nn++]=r; }
    free(res); res=nres; nr=nn; L*=p; }
  fprintf(stderr,"L=%llu residues=%d\n",(unsigned long long)L,nr);
  // sanity: brute check the residue set against direct definition for a sample of m
  // tables for primes 29..1000: tab[p][m mod 4p] = J(p, m)
  int NP=0; int P[200]; for(int p=29;p<1200;p++){int ok=1; for(int d=2;d*d<=p;d++) if(p%d==0){ok=0;break;} if(ok) P[NP++]=p;}
  signed char *tab[200]; for(int i=0;i<NP;i++){ int M=4*P[i]; tab[i]=malloc(M); for(int r=0;r<M;r++) tab[i][r]= (r%2)? jacobi(P[i], r + (u64)M*1000) : 0; }
  u64 found=0, cand=0, fb=0;
  #pragma omp parallel for schedule(dynamic,64) reduction(+:found,cand,fb)
  for(int i=0;i<nr;i++){
    for(u64 m=res[i]; m<=X; m+=L){
      if(m<=529) continue;
      cand++;
      u64 s=isqrt(m); int ok=0; // ok=1 means witness found with p<=s
      for(int j=0;j<NP;j++){ u64 p=P[j]; if(p>s) break; if(tab[j][m%(4*p)]!=1){ ok=1; break; } }
      if(!ok){ fb++; // fallback direct Jacobi on all k<=s
        if(P[NP-1] < s){ for(u64 k=2;k<=s;k++) if(jacobi(k,m)!=1){ok=1;break;} }
        if(!ok){
          #pragma omp critical
          { printf("EXCEPTION m=%llu\n",(unsigned long long)m); fflush(stdout);} found++; }
      }
    }
  }
  printf("fb=%llu ",(unsigned long long)fb); printf("X=%llu candidates=%llu exceptions(>529)=%llu\n",(unsigned long long)X,(unsigned long long)cand,(unsigned long long)found);
  return 0;
}
