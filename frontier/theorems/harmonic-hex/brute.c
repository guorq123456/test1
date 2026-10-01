/* Brute-force A228016 directly from its definition, with rigorous interval arithmetic.
   H(k)*2^120 is enclosed in [L_k, L_k + k] where L_k = sum_{j<=k} floor(2^120/j).
   Sequence (with x=1,y=5):  c_{-1}=0, c_0=5,
   c_n = least k with H(k) - H(c_{n-1}) > H(c_{n-1}) - H(c_{n-2})   (n>=1), and A228016(n)=c_n.
   Scans k = 1,2,3,... once; every comparison H(k) vs threshold must be certified, else abort. */
#include <stdio.h>
#include <stdlib.h>
typedef unsigned __int128 u128;
static void pr(u128 x){ char b[50]; int i=49; b[i]=0; do{ b[--i]='0'+(int)(x%10); x/=10;}while(x); printf("%s",b+i); }
int main(int argc,char**argv){
  unsigned long long K = argc>1 ? strtoull(argv[1],0,10) : 1000000ULL;
  const u128 S = ((u128)1)<<120;
  u128 L=0; unsigned long long k;
  /* intervals for H(c_{n-2}), H(c_{n-1}) */
  u128 Lb=0,Ub=0;            /* H(0)=0 exactly */
  u128 La=0,Ua=0;            /* to be set to H(5) */
  int n=0; /* number of terms found so far; c_0=5 handled as pseudo-term */
  u128 Tlo=0,Thi=0; int have_T=0;
  for(k=1;k<=K;k++){
    L += S/(u128)k;  u128 U = L + (u128)k;
    if(k==5 && !have_T){ La=L; Ua=U; Tlo = 2*La - Ub; Thi = 2*Ua - Lb; have_T=1; continue; }
    if(!have_T) continue;
    if(U <= Tlo) continue;              /* certified H(k) <= T */
    if(L >  Thi){                        /* certified H(k) >  T  -> new term */
      n++; printf("a(%d) = %llu   [margin above T: >= ",n,k); pr((L-Thi)>>40); printf(" * 2^-80; below at k-1 certified]\n");
      fflush(stdout);
      Lb=La; Ub=Ua; La=L; Ua=U; Tlo = 2*La - Ub; Thi = 2*Ua - Lb; continue;
    }
    printf("AMBIGUOUS at k=%llu\n",k); return 1;
  }
  printf("scanned k up to %llu, found %d terms\n",K,n); return 0;
}
