#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
typedef uint64_t u64;
static int jacobi(u64 a, u64 n){ int r=1; a%=n;
  while(a){ int tz=__builtin_ctzll(a); a>>=tz;
    if((tz&1)&&((n&7)==3||(n&7)==5)) r=-r;
    if((a&3)==3&&(n&3)==3) r=-r;
    u64 t=a; a=n%t; n=t; }
  return n==1?r:0; }
int main(int argc,char**argv){
  u64 X=strtoull(argv[1],0,10); char*c=calloc(X+1,1);
  for(u64 i=2;i*i<=X;i++) if(!c[i]) for(u64 j=i*i;j<=X;j+=i) c[j]=1;
  u64 np=0, failA=0, big=0, maxratio_q=0; double maxratio=0;
  for(u64 q=3;q<=X;q+=2) if(!c[q]){ np++;
    u64 n=1; while(jacobi(n,q)==1) n++;
    if(!(n*(n-1)<q)) {failA++; printf("Lemma A fails q=%llu n=%llu\n",(unsigned long long)q,(unsigned long long)n);}
    double r=(double)n*n/q; if(r>maxratio && q>23){maxratio=r; maxratio_q=q;}
    if(n*n>q){ big++;
      int ok = jacobi(q-1,q)==-1; for(u64 x=q-n+1;x<=q-1;x++) if(jacobi(x,q)!=-1) ok=0;
      printf("n^2>q: q=%llu n=%llu LemmaB=%s\n",(unsigned long long)q,(unsigned long long)n, ok?"holds":"FAILS");
    }
  }
  printf("primes=%llu LemmaA failures=%llu n^2>q count=%llu; max n^2/q for q>23: %.6f at q=%llu\n",(unsigned long long)np,(unsigned long long)failA,(unsigned long long)big,maxratio,(unsigned long long)maxratio_q);
}
