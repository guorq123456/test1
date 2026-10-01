// Lemma C: for odd n>=29, odd q in (n(n-1), n^2): exists a<=b<=n-1, a>=1, q-n+2 <= 2ab <= q-1.
// (1) check the paper's explicit construction exhaustively for odd n in [3, NMAX];
// (2) for small n where the construction fails, check whether ANY (a,b) exists (brute force).
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
typedef long long ll;
static ll isqrt(ll x){ ll r=(ll)sqrtl((long double)x); while(r*r>x) r--; while((r+1)*(r+1)<=x) r++; return r; }
static ll iceilsqrt(ll x){ ll r=isqrt(x); return r*r==x? r : r+1; }
int main(int argc,char**argv){
  ll NMAX=atoll(argv[1]); ll pairs=0, fails=0;
  for(ll n=3;n<=NMAX;n+=2){
    ll nf=0;
    for(ll q=n*(n-1)+1; q<n*n; q+=2){ // q odd: n(n-1) even so +1 is odd
      ll N=(q-n+2)/2; ll s=iceilsqrt(N); ll D=s*s-N; ll t=isqrt(D); ll a=s-t, b=s+t;
      int ok = (a>=1 && a<=b && b<=n-1 && 2*a*b>=q-n+2 && 2*a*b<=q-1);
      if(!ok){ nf++;
        if(n>=29){ printf("CONSTRUCTION FAIL n=%lld q=%lld\n",n,q); }
      }
      if(n>=29) pairs++;
    }
    if(nf && n<29){
      // any a,b at all? (for each failing q)
      ll nofix=0;
      for(ll q=n*(n-1)+1; q<n*n; q+=2){ int ex=0; for(ll a=1;a<n&&!ex;a++) for(ll b=a;b<n;b++){ ll v=2*a*b; if(v>=q-n+2&&v<=q-1){ex=1;break;} } if(!ex) nofix++; }
      printf("n=%lld: construction fails for %lld q's; q's with no (a,b) at all: %lld\n",n,nf,nofix);
    }
    if(n>=29) fails+=nf;
  }
  printf("n odd in [29,%lld]: pairs=%lld construction failures=%lld\n",NMAX,pairs,fails);
  return 0;
}
