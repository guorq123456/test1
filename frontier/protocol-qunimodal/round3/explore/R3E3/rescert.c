/* Residue-level certificate (TP, E, O) of R2E2 Theorem R, own C implementation.
   Usage: rescert r KLO KHI [skip45]
   Enumerates all residue multisets rho (counts c_1..c_{r-1}) with KLO <= k <= KHI.
   If skip45=1, skips (fit-box exclusion (a)) multisets with exactly 4 or 5 middle residues (k>=20).
   Prints counts of checked / skipped / failures (and first failures).
   Exact arithmetic in __int128 (A <= (r-1)^k must stay < 2^126: checked); f saturates at 2^100. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef __int128 I;
#define MAXS 2000
static int r,KLO,KHI,skip45;
static long long nchk=0,nskip=0,nfail=0;
static I A[MAXS], e[MAXS], dd[MAXS+64];
static I fsat[200][MAXS+64]; /* f for k (index k) */
static const I SAT=((I)1)<<100;
static int cnt[64];
static void mkf(int k,int L){ /* 1/((1-q)^{k-1}(1-q^r)) saturating */
  I *f=fsat[k]; for(int i=0;i<L;i++) f[i]=(i%r==0)?1:0;
  for(int t=0;t<k-1;t++) for(int i=1;i<L;i++){ f[i]+=f[i-1]; if(f[i]>SAT) f[i]=SAT; }
}
static int sig, L;
static I tau[64];
static I D_(int y){ return (y<0)?0:dd[y]; }
static I Q_(int u){ int t=((u%r)+r)%r; return D_(u)-tau[t]; }
static int ND(int K){
  for(int x=(K-r)/2-2; 2*x<K; x++){ if(2*x<K-r) continue; if(Q_(K-x)<D_(x)) return 0; }
  return 1;
}
static void evaluate(int mcount){
  /* A of length sig+1 is current product of [rho] for rho>=2 */
  memset(e,0,sizeof(I)*(sig+3));
  for(int i=0;i<=sig;i++){ e[i]+=A[i]; e[i+1]-=A[i]; }
  for(int t=0;t<r;t++) tau[t]=0;
  for(int i=0;i<=sig+1;i++) tau[i%r]+=e[i];
  L=sig+4*r+8;
  for(int i=0;i<L;i++){ dd[i]=(i<=sig+1?e[i]:0)+(i>=r?dd[i-r]:0); }
  /* TP */
  int tp=1;
  for(int z=-r; z<=sig+1; z++) if(Q_(z)<0){ int v=sig+1-2*z; int fl = (v>=0)? v/r : -((-v+r-1)/r); if(fl%2!=0){tp=0;break;} }
  int m1lo=KLO-mcount; if(m1lo<0) m1lo=0;
  for(int c1=m1lo; mcount+c1<=KHI; c1++){
    int k=mcount+c1;
    int mid=0; for(int t=2;t<=r-2;t++) mid+=cnt[t];
    if(skip45 && k>=20 && (mid==4||mid==5)){ nskip++; continue; }
    nchk++;
    int ok=tp;
    if(ok){
      I *f=fsat[k]; int mu=-1000000;
      for(int u=-r; u<sig+2*r; u++){ I fu=(u>=0)?f[u]:0; if(fu<tau[((u%r)+r)%r]) mu=u; }
      for(int K=2*mu-4*r; K<=sig+1-2*r && ok; K++){
        if(((K-(sig+1))%(2*r)+2*r)%(2*r)==0 && K>=2*mu){ if(!ND(K)) ok=0; }
        if(((K-(sig+1+r))%(2*r)+2*r)%(2*r)==0 && K>=2*mu+3*r){ if(!ND(K)) ok=0; }
      }
    }
    if(!ok){ nfail++; if(nfail<=20){ printf("FAIL k=%d c1=%d counts:",k,c1); for(int t=2;t<r;t++) printf(" %d",cnt[t]); printf(" tp=%d\n",tp);} }
  }
}
static void rec(int t,int m){ /* choose counts for residues t..r-1 (t>=2) */
  if(t==r){ evaluate(m); return; }
  I save[MAXS]; int ssig=sig; memcpy(save,A,sizeof(I)*(sig+1));
  for(int c=0; m+c<=KHI; c++){
    cnt[t]=c; rec(t+1,m+c);
    if(m+c+1>KHI) break;
    /* multiply A by [t] */
    int ns=sig+t-1; I nb[MAXS]; I s=0;
    for(int x=0;x<=ns;x++){ if(x<=sig) s+=A[x]; if(x-t>=0 && x-t<=sig) s-=A[x-t]; nb[x]=s; }
    sig=ns; memcpy(A,nb,sizeof(I)*(sig+1));
    if(A[sig/2] > (((I)1)<<120)){ fprintf(stderr,"overflow risk\n"); exit(2);}
  }
  cnt[t]=0; sig=ssig; memcpy(A,save,sizeof(I)*(sig+1));
}
int main(int argc,char**argv){
  r=atoi(argv[1]); KLO=atoi(argv[2]); KHI=atoi(argv[3]); skip45=argc>4?atoi(argv[4]):0;
  for(int k=1;k<=KHI;k++) mkf(k,(r-1)*KHI+4*r+16);
  A[0]=1; sig=0; rec(2,0);
  printf("r=%d k in [%d,%d] checked=%lld skipped=%lld fails=%lld\n",r,KLO,KHI,nchk,nskip,nfail);
  return 0;
}
