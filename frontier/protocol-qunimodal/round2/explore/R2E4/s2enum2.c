// Exhaustive S2 check over multisets, with pattern histogram and near-miss scores.
// usage: s2enum2 r k vmin vmax minmid thresh [maxprint]
// Pattern = membership string of U on b=F+1..T6 (T1: b<=1+F unimodal, Thm C: b>T6 not; both rechecked here).
// Near-miss score: min over b in (B*,T6] whose joining U would violate S2, of relative deficit
//   ndef(b)=sum_i max(0,d_{i-rb}-d_i)/max_i|d_i|.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef __int128 I;
static int r,k,vmin,vmax,minmid; static int a[64]; static double thresh;
static I A[8192], d[16384];
static long long ninst=0,nviol=0,ngap=0,nskip=0,nbeyond=0,nlowfail=0,nshort=0;
#define NP 4096
static char pats[NP][64]; static long long pcnt[NP]; static int np=0;
static double best=1e9; static char bestdesc[512];
static double unimodal_b(int D,int b,int*ok){
  // returns normalized negative mass: sum_i max(0,d_{i-rb}-d_i) / max_i |d_i| (0 iff unimodal)
  int N=D+r*(b-1), h=N/2; long double neg=0, mx=1; *ok=1;
  for(int i=1;i<=h;i++){ I y=(i-r*b>=0? d[i-r*b]:0); I x=d[i]-y; long double ad=(long double)(d[i]<0?-d[i]:d[i]); if(ad>mx) mx=ad;
    if(x<0){ *ok=0; neg+=(long double)(-x);} }
  return (double)(neg/mx);
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
  static char U[4096]; static double def[4096]; int Bs=0;
  for(int b=1;b<=bmax;b++){ int ok; def[b]=unimodal_b(D,b,&ok); U[b]=ok; if(ok) Bs=b; }
  for(int b=1;b<=F+1;b++) if(!U[b]) nlowfail++;
  int miss=0, missat=-1, shape; for(int b=1;b<=Bs;b++) if(!U[b]){miss++;missat=b;}
  if(miss==0) shape=0; else if(miss==1&&missat==Bs-1) shape=1; else shape=2;
  int par=((Bs-1-F)%2==0);
  if(shape==1) ngap++;
  if(Bs>T6) nbeyond++;
  if(Bs<T6) nshort++;
  // pattern
  char p[64]; int L2=T6-F; if(L2>60) L2=60; for(int j=0;j<L2;j++) p[j]=U[F+1+j]?'1':'0'; p[L2]=0;
  int f=-1; for(int j=0;j<np;j++) if(!strcmp(pats[j],p)){f=j;break;}
  if(f<0 && np<NP){ strcpy(pats[np],p); pcnt[np]=0; f=np++; } if(f>=0) pcnt[f]++;
  if(shape==2||!par||Bs>T6){ nviol++;
    printf("VIOL r=%d a=(",r); for(int i=0;i<k;i++) printf("%d%s",a[i],i<k-1?",":""); printf(") F=%d T6=%d B*=%d shape=%d par=%d U=",F,T6,Bs,shape,par);
    for(int b=1;b<=bmax;b++) if(U[b]) printf("%d,",b); printf("\n"); fflush(stdout);}
  // near miss
  double sc=1e9; int scb=-1;
  for(int b=Bs+1;b<=T6;b++){ if(shape==0 && b==Bs+2) continue; if(def[b]<sc){sc=def[b];scb=b;} }
  if(sc<best){ best=sc; char*q=bestdesc; q+=sprintf(q,"r=%d a=(",r); for(int i=0;i<k;i++) q+=sprintf(q,"%d%s",a[i],i<k-1?",":"");
    sprintf(q,") F=%d T6=%d B*=%d shape=%d flip_b=%d rdef=%.3e pat=%s",F,T6,Bs,shape,scb,sc,p); }
  if(sc<thresh){ printf("NEAR r=%d a=(",r); for(int i=0;i<k;i++) printf("%d%s",a[i],i<k-1?",":""); printf(") F=%d T6=%d B*=%d shape=%d flip_b=%d rdef=%.3e pat=%s\n",F,T6,Bs,shape,scb,sc,p);}
}
static void rec(int pos,int lo,int mid){
  if(pos==k){ if(mid>=minmid) check(); return; }
  for(int v=lo;v<=vmax;v++){ if(v%r==0) continue; int m=(v%r>=2&&v%r<=r-2);
    if(mid+m+(k-pos-1)<minmid) continue;
    a[pos]=v; rec(pos+1,v,mid+m); }
}
int main(int argc,char**argv){
  r=atoi(argv[1]);k=atoi(argv[2]);vmin=atoi(argv[3]);vmax=atoi(argv[4]);minmid=atoi(argv[5]);thresh=atof(argv[6]);
  rec(0,vmin,0);
  printf("DONE r=%d k=%d v=[%d,%d] minmid=%d inst=%lld gap=%lld viol=%lld beyondT6=%lld lowfail=%lld short=%lld skipped=%lld\n",r,k,vmin,vmax,minmid,ninst,ngap,nviol,nbeyond,nlowfail,nshort,nskip);
  printf("BEST %s\n",bestdesc);
  printf("PATTERNS");
  for(int j=0;j<np;j++) printf(" %s:%lld",pats[j][0]?pats[j]:"-",pcnt[j]); printf("\n");
  return 0;
}
