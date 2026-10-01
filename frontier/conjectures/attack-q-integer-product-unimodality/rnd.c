// Random large-k tests of Conjecture 5.4 with __int128 coefficients.
// Checks: sufficiency (b<=F+1 => unimodal); r=2: unimodal iff b<=F+1; r=3: unimodal iff b<=F+1+2*floor(S/6);
// for every r: the set of unimodal b is an initial segment {1..bmax}.
// usage: rnd seed iters kmin kmax rmin rmax amin amax
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
typedef __int128 i128;
static unsigned long long st;
static unsigned long long rnd(){ st^=st<<13; st^=st>>7; st^=st<<17; return st; }
int main(int argc,char**argv){
  st=strtoull(argv[1],0,10)*2654435761ULL+12345; long iters=atol(argv[2]);
  int kmin=atoi(argv[3]),kmax=atoi(argv[4]),rmin=atoi(argv[5]),rmax=atoi(argv[6]),amin=atoi(argv[7]),amax=atoi(argv[8]);
  int maxdeg=kmax*amax+10; int Cmax=maxdeg*3+rmax*10+100;
  i128 *P=malloc(sizeof(i128)*(maxdeg+1)),*Q=malloc(sizeof(i128)*(maxdeg+1)),*C=malloc(sizeof(i128)*(Cmax+1));
  long nsuff=0,nr3=0,nr2=0,nnonmono=0,ntested=0,nlemma=0;
  for(long it=0;it<iters;it++){
    int r=rmin+rnd()%(rmax-rmin+1), k=kmin+rnd()%(kmax-kmin+1);
    int a[256]; double lg=0;
    for(int i=0;i<k;i++){ int v; do{ v=amin+rnd()%(amax-amin+1);}while(v%r==0); a[i]=v; lg+=log2(v);}
    if(lg>120) continue;
    // sort
    for(int i=1;i<k;i++){int v=a[i],j=i-1;while(j>=0&&a[j]>v){a[j+1]=a[j];j--;}a[j+1]=v;}
    int D=0; P[0]=1;
    for(int i=0;i<k;i++){ int v=a[i]; int nd=D+v-1; i128 run=0;
      for(int t=0;t<=nd;t++){ if(t<=D) run+=P[t]; if(t-v>=0&&t-v<=D) run-=P[t-v]; Q[t]=run; }
      D=nd; memcpy(P,Q,sizeof(i128)*(D+1)); }
    int F=0,S=0,S2=0; for(int i=0;i<k;i++){F+=a[i]/r; S+=a[i]%r-1; if(a[i]%r==2) S2++;}
    int bcap=(D+2*r+r-1)/r+1+1;
    if(D+r*(bcap-1)>Cmax) continue;
    memset(C,0,sizeof(i128)*(D+r*(bcap-1)+1)); for(int t=0;t<=D;t++) C[t]=P[t];
    int seenfail=0,bmax=1;
    ntested++;
    for(int b=2;b<=bcap;b++){
      int sh=r*(b-1); for(int t=0;t<=D;t++) C[t+sh]+=P[t];
      int E=D+sh,u=1; for(int t=0;t<E/2;t++) if(C[t]>C[t+1]){u=0;break;}
      if(u){ if(seenfail){nnonmono++; printf("NONMONO r=%d b=%d F=%d a=",r,b,F); for(int i=0;i<k;i++) printf("%d,",a[i]); printf("\n");} bmax=b; } else seenfail=1;
      if(b<=F+1 && !u){ nsuff++; printf("SUFF r=%d a=",r); for(int i=0;i<k;i++) printf("%d,",a[i]); printf(" b=%d\n",b); fflush(stdout);}
      if(u && r*(b-1)>=D+2*r){ nlemma++; printf("LEMMA?? r=%d\n",r);}
    }
    if(r==2 && bmax!=F+1){ nr2++; printf("R2RULE r=2 a=");for(int i=0;i<k;i++) printf("%d,",a[i]); printf(" bmax=%d F=%d\n",bmax,F);}
    if(r==3 && bmax!=F+1+2*(S/6)){ nr3++; printf("R3RULE a=");for(int i=0;i<k;i++) printf("%d,",a[i]); printf(" bmax=%d F=%d S=%d\n",bmax,F,S);}
  }
  printf("tested=%ld suff_fail=%ld r2rule_fail=%ld r3rule_fail=%ld nonmono=%ld lemma_fail=%ld\n",ntested,nsuff,nr2,nr3,nnonmono,nlemma);
  return 0;
}
