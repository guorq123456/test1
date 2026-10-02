/* Certificate C2 for the r=4 proof: exhaustive check over all multisets of k' (1..KMAX) parts >= 2,
   no part divisible by 4, with parts capped: exact sizes 2,3,5,6,7,9,10,11 and lumped types
   L1=13 (any part >=13, ==1 mod 4), L2=14 (>=14, ==2), L3=15 (>=15, ==3).
   For x <= X=12 the tail alpha_0..alpha_X is exact for every realization (parts >= X+1 act as 1/(1-q)).
   For each multiset with n2>=1 (n2 = #parts ==2 mod 4), V = 2^floor((n2-1)/2), and each gap g in {1,2,3}:
   every candidate x = x_{n*+1} >= g+4 must be covered:
     x <= X : PRE (some chain step below x increases => x is before the peak, impossible) or
              LP  (delta_x - delta_{x-g} >= delta_{x-g-4}) or  TT (exact alternating tail sum >= V);
              positions x >= (D+1)/2 are skipped only when the multiset has no lumped part (then D is exact).
     x >  X : for each class mod 4 the largest chain position xc<=X (xc>=g+4 not required) must satisfy PRE or TT.
   Only the (gap, class mod 4) of x_{n*+1} allowed by sigma (proof Lemma 6) are checked.
   Prints counts and any uncovered case. */
#include <stdio.h>
#include <stdlib.h>
#define X 12
static const int sz[11]={2,3,5,6,7,9,10,11,13,14,15};
static const int lump[11]={0,0,0,0,0,0,0,0,1,1,1};
static int cnt[11]; static long long nms=0, nchk=0, unc=0; static int KMAX;
static long long dl(const long long*al,int x){ if(x<0) return 0; return al[x]-(x>=1?al[x-1]:0); }
static void evaluate(const long long *al,int kp){
  int n2=cnt[0]+cnt[3]+cnt[6]+cnt[9]; if(n2<1) return;
  long long V=1LL<<((n2-1)/2);
  int haslump=cnt[8]+cnt[9]+cnt[10]; long D=0; for(int t=0;t<11;t++) D+=(long)cnt[t]*(sz[t]-1);
  nms++;
  int sig=0; for(int t=0;t<11;t++) sig+=cnt[t]*(sz[t]%4-1);
  for(int g=1;g<=3;g++){
    int cls;
    if(sig%2){ if(g!=2) continue; cls=((sig-1)/2)%4; }
    else { if(g==2) continue; cls = (g==1)? (sig/2+3)%4 : (sig/2)%4; }
    /* pre[x]: 1 if some chain step at or below x (chain x, x-g, x-4, x-4-g, ...) increases */
    for(int x=g+4;x<=X;x++){
      if(x%4!=cls) continue;
      if(!haslump && 2*x>=D+1) continue;
      nchk++;
      int pre=0; long long T=0;
      for(int t=x;t>=0;t-=4){
        long long a1=dl(al,t), a2=dl(al,t-g), a3=dl(al,t-4);
        if(a1<a2) pre=1;               /* y_j < y_{j+1} */
        if(t-g>=0 && a2<a3) pre=1;     /* y_{j+1} < y_{j+2} */
        T+=a1-a2;
      }
      if(pre) continue;
      if(dl(al,x)-dl(al,x-g)>=dl(al,x-g-4)) continue;
      if(T>=V) continue;
      unc++; if(unc<=30){ printf("UNCOVERED x=%d g=%d kp=%d V=%lld cnt:",x,g,kp,V); for(int t=0;t<11;t++) printf(" %d",cnt[t]); printf("\n"); }
    }
    /* x > X: per class, largest chain position xc <= X */
    if(haslump || 2*(X+1)<D+1){
      for(int xc=X-3; xc<=X; xc++){
        if(xc%4!=cls) continue;
        int pre=0; long long T=0;
        for(int t=xc;t>=0;t-=4){
          long long a1=dl(al,t), a2=dl(al,t-g), a3=dl(al,t-4);
          if(a1<a2) pre=1; if(t-g>=0 && a2<a3) pre=1; T+=a1-a2; }
        nchk++;
        if(pre||T>=V) continue;
        unc++; if(unc<=30){ printf("UNCOVERED-TAIL xc=%d g=%d kp=%d V=%lld T=%lld cnt:",xc,g,kp,V,T); for(int t=0;t<11;t++) printf(" %d",cnt[t]); printf("\n"); }
      }
    }
  }
}
static void rec(int type,int kp,const long long *al){
  if(kp>=1) evaluate(al,kp);
  if(kp==KMAX) return;
  for(int t=type;t<11;t++){
    long long nb[X+1]; int a=sz[t]; long long s=0;
    for(int x=0;x<=X;x++){ s+=al[x]; if(x-a>=0) s-=al[x-a]; nb[x]=s; }
    cnt[t]++; rec(t,kp+1,nb); cnt[t]--;
  }
}
int main(int argc,char**argv){
  KMAX=atoi(argv[1]); long long al[X+1]={0}; al[0]=1;
  rec(0,0,al);
  printf("KMAX=%d multisets(n2>=1)=%lld checks=%lld uncovered=%lld\n",KMAX,nms,nchk,unc);
  return 0;
}
