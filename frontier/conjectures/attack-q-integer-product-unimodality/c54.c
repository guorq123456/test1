// Exhaustive check of Conjecture 5.4 (arXiv:2605.12822).
// P = prod [a_i]_q (a_i in [2,A], r does not divide a_i, sorted multiset), C_b = P * [b]_{q^r}.
// cond(b) := b <= 1 + sum floor(a_i/r).  (r | a_i case is trivially unimodal; skipped.)
// For each b in 2..bcap: check unimodality of C_b (symmetric => check nondecreasing up to middle).
// bcap chosen so that for b > bcap, non-unimodality is guaranteed (periodic-window lemma);
// optional extra slack EXTRA.
// usage: c54 Rmin Rmax kmin kmax A EXTRA [maxprint]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef long long ll;
static int Rmin,Rmax,kmin,kmax,A,EXTRA,maxprint=50,mode=0;
static int r;
static ll *P[64]; static int deg[64];
static int a[64];
static ll *C;
static ll nsuff=0,nnec=0,ncases=0,nchecks=0;
static ll necCount[64]; // per k for current r
static int printedNec[64];
static double maxval=0;

static int is_unimodal_sym(const ll *c,int E){
  int h=E/2;
  for(int t=0;t<h;t++) if(c[t]>c[t+1]) return 0;
  return 1;
}
static void process(int k){
  // P[k] has degree deg[k]
  int D=deg[k]; ll *p=P[k];
  int F=0, S=0; double prod=1;
  for(int i=0;i<k;i++){F+=a[i]/r; S+=(a[i]%r)-1; prod*=a[i];}
  // window lemma: if r(b-1) >= D+2r then non-unimodal. so bcap = smallest b with r(b-1)>=D+2r, minus 1
  int bcap=(D+2*r + r-1)/r + 1; // b-1 >= ceil((D+2r)/r)
  bcap += EXTRA;
  if(prod*bcap>maxval) maxval=prod*bcap;
  int Emax=D+r*(bcap-1);
  memset(C,0,sizeof(ll)*(Emax+1));
  for(int t=0;t<=D;t++) C[t]=p[t];
  ncases++;
  unsigned long long mask=0; int nonmono=0, seenfail=0;
  for(int b=2;b<=bcap;b++){
    int sh=r*(b-1);
    for(int t=0;t<=D;t++) C[t+sh]+=p[t];
    int E=D+sh;
    int u=is_unimodal_sym(C,E);
    int cond=(b<=1+F);
    nchecks++;
    if(cond && !u){
      nsuff++;
      printf("SUFF r=%d k=%d a=",r,k); for(int i=0;i<k;i++) printf("%d%s",a[i],i<k-1?",":""); printf(" b=%d\n",b); fflush(stdout);
    }
    if(!cond){ if(u){ if(b-F-2<64) mask|=1ULL<<(b-F-2); if(seenfail) nonmono=1;} else seenfail=1; }
    if(!cond && u){
      nnec++; necCount[k]++;
      if(printedNec[k]<maxprint){printedNec[k]++;
        printf("NEC r=%d k=%d a=",r,k); for(int i=0;i<k;i++) printf("%d%s",a[i],i<k-1?",":""); printf(" b=%d  (F=%d, S=%d, bmin_viol=%d)\n",b,F,S,F+2); fflush(stdout);}
      if(b>(D+2*r+r-1)/r+1){printf("LEMMA VIOLATION?! r=%d b=%d\n",r,b);}
    }
  }
  if(mode==1 && mask){ int cnt[64]={0}; for(int i=0;i<k;i++) cnt[a[i]%r]++; printf("U r=%d k=%d F=%d S=%d res=",r,k,F,S); for(int m=1;m<r;m++) printf("%d%s",cnt[m],m<r-1?",":""); printf(" mask=%llx nonmono=%d\n",mask,nonmono);}
  if(nonmono) printf("NONMONO r=%d k=%d a0=%d\n",r,k,a[0]);
}
static void rec(int level,int minv){
  // level = number of a's chosen so far; P[level] current
  if(level>=kmin) process(level);
  if(level==kmax) return;
  for(int v=minv; v<=A; v++){
    if(v%r==0) continue;
    a[level]=v;
    int D=deg[level], nd=D+v-1;
    ll *src=P[level], *dst=P[level+1];
    // dst = src * [v]_q via sliding window
    ll run=0;
    for(int t=0;t<=nd;t++){
      if(t<=D) run+=src[t];
      if(t-v>=0 && t-v<=D) run-=src[t-v];
      dst[t]=run;
    }
    deg[level+1]=nd;
    rec(level+1,v);
  }
}
int main(int argc,char**argv){
  Rmin=atoi(argv[1]);Rmax=atoi(argv[2]);kmin=atoi(argv[3]);kmax=atoi(argv[4]);A=atoi(argv[5]);EXTRA=atoi(argv[6]);
  if(argc>7) maxprint=atoi(argv[7]);
  if(argc>8) mode=atoi(argv[8]);
  int maxdeg=kmax*A+10;
  for(int i=0;i<=kmax;i++) P[i]=calloc(maxdeg+1,sizeof(ll));
  int Cmax=maxdeg+ Rmax*(maxdeg/2+EXTRA+10)+10;
  C=calloc(Cmax+1,sizeof(ll));
  for(r=Rmin;r<=Rmax;r++){
    memset(necCount,0,sizeof(necCount)); memset(printedNec,0,sizeof(printedNec));
    P[0][0]=1; deg[0]=0;
    rec(0,2);
    printf("r=%d done: necessity-failure counts by k:",r); for(int k=kmin;k<=kmax;k++) printf(" k%d:%lld",k,necCount[k]); printf("\n"); fflush(stdout);
  }
  printf("TOTAL cases=%lld checks=%lld suff_fail=%lld nec_fail=%lld maxbound=%.3g\n",ncases,nchecks,nsuff,nnec,maxval);
  return 0;
}
