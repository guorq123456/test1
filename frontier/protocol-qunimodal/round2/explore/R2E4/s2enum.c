// Exhaustive S2 check over multisets. usage: s2enum r k vmin vmax [minmid]
// enumerates sorted a_1<=...<=a_k in [vmin,vmax], r divides none, #middle>=minmid,
// computes U over b in [1, T6+3] using d-criterion (b<=1+F assumed unimodal by T1 but also checked),
// prints any S2 violation (and any U beyond T6). Uses __int128; skips if prod a_i >= 2^120.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef __int128 I;
static int r,k,vmin,vmax,minmid; static int a[64];
static I A[8192], d[16384];
static long long ninst=0,nviol=0,ngap=0,nskip=0,nbeyond=0;
static int unimodal_b(int D,int b){
  int N=D+r*(b-1), h=N/2;
  for(int i=1;i<=h;i++){ I x=d[i]-(i-r*b>=0? d[i-r*b]:0); if(x<0) return 0; }
  return 1;
}
static void check(void){
  long double lp=1; for(int i=0;i<k;i++) lp*=a[i]; if(lp>1.0e36L){nskip++;return;}
  int D=0; A[0]=1;
  for(int i=0;i<k;i++){ int Ai=a[i], nd=D+Ai-1; I s=0; static I tmp[8192];
    for(int t=0;t<=nd;t++){ if(t<=D) s+=A[t]; if(t-Ai>=0&&t-Ai<=D) s-=A[t-Ai]; tmp[t]=s; }
    D=nd; memcpy(A,tmp,sizeof(I)*(D+1)); }
  int F=0; for(int i=0;i<k;i++) F+=a[i]/r;
  I G[64]; for(int t=0;t<r;t++) G[t]=0; for(int i=0;i<=D;i++) G[i%r]+=A[i];
  int mu=r-1; for(int t=r-1;t>=0;t--){ int ok=1; for(int j=t;j<r-1;j++) if(G[j]<G[j+1]) ok=0; if(ok) mu=t; else break; }
  int T6=1+(D+1-2*mu)/r;
  int bmax=T6+3; int L=(D+r*(bmax-1))/2+2;
  for(int i=0;i<L;i++){ I Ai=i<=D?A[i]:0, Aim=(i>=1&&i-1<=D)?A[i-1]:0; d[i]=(i>=r?d[i-r]:0)+Ai-Aim; }
  ninst++;
  char U[4096]; int Bs=0;
  for(int b=1;b<=bmax;b++){ U[b]=unimodal_b(D,b); if(U[b]) Bs=b; }
  int shape; // 0 interval,1 gap,2 bad
  int miss=0, missat=-1; for(int b=1;b<=Bs;b++) if(!U[b]){miss++;missat=b;}
  if(miss==0) shape=0; else if(miss==1&&missat==Bs-1) shape=1; else shape=2;
  int par=((Bs-1-F)%2==0);
  if(shape==1) ngap++;
  if(Bs>T6) nbeyond++;
  if(shape==2||!par||Bs>T6){ nviol++;
    printf("VIOL r=%d a=(",r); for(int i=0;i<k;i++) printf("%d%s",a[i],i<k-1?",":""); printf(") F=%d T6=%d B*=%d shape=%d par=%d U=",F,T6,Bs,shape,par);
    for(int b=1;b<=bmax;b++) if(U[b]) printf("%d,",b); printf("\n"); fflush(stdout);}
}
static void rec(int pos,int lo,int mid){
  if(pos==k){ if(mid>=minmid) check(); return; }
  for(int v=lo;v<=vmax;v++){ if(v%r==0) continue; int m=(v%r>=2&&v%r<=r-2);
    if(mid+m+(k-pos-1)<minmid) continue;
    a[pos]=v; rec(pos+1,v,mid+m); }
}
int main(int argc,char**argv){
  r=atoi(argv[1]);k=atoi(argv[2]);vmin=atoi(argv[3]);vmax=atoi(argv[4]);minmid=argc>5?atoi(argv[5]):3;
  rec(0,vmin,0);
  printf("DONE r=%d k=%d v=[%d,%d] minmid=%d inst=%lld gap=%lld viol=%lld beyondT6=%lld skipped=%lld\n",r,k,vmin,vmax,minmid,ninst,ngap,nviol,nbeyond,nskip);
  return 0;
}
